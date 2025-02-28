from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
import time
from time import sleep
from litellm import completion
import requests
from bs4 import BeautifulSoup

@csrf_exempt
@require_http_methods(["POST"])
def process_message_web_search(request):
    try:
       # Check if the request is multipart (FormData submission)
        if request.content_type.startswith('multipart/form-data'):
            prompt = request.POST.get('message')
            model_choice = request.POST.get('model', 'calista:latest')
        else:
            data = json.loads(request.body)
            prompt = data.get('message')
            model_choice = data.get('model', 'calista:latest')
        
        if not prompt:
            return JsonResponse({'error': 'No message provided'}, status=400)

        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

        tools, available_functions = [], {}
        newly_learned_urls = []  # Tracks URLs learned in this run only
        MAX_TOOL_OUTPUT_LENGTH = 5000  

        def register_tool(name, func, description, parameters):
            nonlocal tools
            # Remove any previously registered tool with the same name.
            tools = [tool for tool in tools if tool["function"]["name"] != name]
            available_functions[name] = func
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": parameters,
                        "required": list(parameters.keys())
                    }
                }
            })
            print(f"{OKGREEN}Registered tool: {name}{ENDC}")

        def serialize_tool_result(tool_result, max_length=MAX_TOOL_OUTPUT_LENGTH):
            try:
                serialized_result = json.dumps(tool_result)
            except TypeError:
                serialized_result = str(tool_result)
            if len(serialized_result) > max_length:
                return serialized_result[:max_length] + (
                    f"\n\n(Note: Result was truncated to {max_length} characters out of {len(serialized_result)})"
                )
            return serialized_result

        def call_tool(function_name, args):
            func = available_functions.get(function_name)
            if not func:
                err_msg = f"Error: Tool '{function_name}' not found."
                print(f"{WARNING}{err_msg}{ENDC}")
                return err_msg
            try:
                return func(**args)
            except Exception as e:
                err_msg = f"Error executing '{function_name}': {e}"
                print(f"{FAIL}{err_msg}{ENDC}")
                return err_msg

        def task_completed():
            return "Task marked as completed."

        def websearch(query, num_results=5):
            """
            Performs a web search using DuckDuckGo and returns up to 'num_results' search results.
            """
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.post(
                    "https://html.duckduckgo.com/html", 
                    data={"q": query}, 
                    timeout=10, 
                    headers=headers
                )
                soup = BeautifulSoup(response.text, "html.parser")
                results = []
                for a in soup.find_all("a", class_="result__a"):
                    title = a.get_text(strip=True)
                    url = a.get("href")
                    results.append({"title": title, "url": url})
                    if len(results) >= num_results:
                        break
                if not results:
                    return "No results found."
                return results
            except Exception as e:
                return f"Error during web search: {e}"

        def fetch_website_content(url):
            """
            Fetches content from the specified URL and extracts a title and text content.
            Supports both HTML and PDF content types.
            Additionally, returns the time taken to access the website.
            """
            start_time = time.time()
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, timeout=10, verify=False, headers=headers)
                access_time = time.time() - start_time
                if response.status_code != 200:
                    return f"Error: Received status code {response.status_code} while fetching {url} (accessed in {access_time:.2f}s)"
                
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                    try:
                        import io
                        from PyPDF2 import PdfReader
                        reader = PdfReader(io.BytesIO(response.content))
                        title = "PDF Document"
                        if reader.metadata and reader.metadata.title:
                            title = reader.metadata.title
                        texts = [page.extract_text() for page in reader.pages if page.extract_text()]
                        text = "\n".join(texts) if texts else "No text content could be extracted from the PDF."
                        return {"title": title, "content": text, "access_time": f"{access_time:.2f} seconds"}
                    except Exception as e:
                        return f"Error processing PDF: {e} (accessed in {access_time:.2f}s)"
                else:
                    soup = BeautifulSoup(response.text, "html.parser")
                    title_tag = soup.find("title")
                    title = title_tag.get_text(strip=True) if title_tag else "No title found"
                    paragraphs = soup.find_all("p")
                    content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                    if not content:
                        content = soup.get_text(separator="\n", strip=True)
                    return {"title": title, "content": content, "access_time": f"{access_time:.2f} seconds"}
            except Exception as e:
                access_time = time.time() - start_time
                return f"Error fetching website content: {e} (accessed in {access_time:.2f}s)"

        def learn_from_url(url):
            try:
                kb_file = "knowledge_base.json"
                kb = {}
                if os.path.exists(kb_file):
                    with open(kb_file, "r", encoding="utf-8") as f:
                        kb = json.load(f)
                content = fetch_website_content(url)
                # If a 403 error is encountered, skip saving the data
                if isinstance(content, str) and "Received status code 403" in content:
                    return f"Skipped learning from {url} due to 403 Forbidden error."
                kb[url] = content
                with open(kb_file, "w", encoding="utf-8") as f:
                    json.dump(kb, f, indent=2, ensure_ascii=False)
                if url not in newly_learned_urls:
                    newly_learned_urls.append(url)
                return f"Content from {url} has been learned and saved."
            except Exception as e:
                return f"Error during learning from URL {url}: {e}"

        def learn_all_search_results(search_results):
            if isinstance(search_results, str):
                yield "No valid search results to learn from.\n"
                return
            for result in search_results:
                url = result.get("url")
                if url:
                    yield (
                        "\n"
                        "====================================\n"
                        "  Learning Content from URL\n"
                        "====================================\n"
                        f"URL: {url}\n"
                        f""
                    )
                    message = learn_from_url(url)
                    yield f"Result: {message}\n\n"
                    sleep(1)

        def print_search_results(search_results):
            """
            Prints website search results with color enhancements.
            """
            print(f"{HEADER}--- Website Link Search Results ---{ENDC}")
            if isinstance(search_results, str):
                print(f"{WARNING}{search_results}{ENDC}")
            else:
                for i, result in enumerate(search_results):
                    title = result.get("title", "No Title")
                    url = result.get("url", "No URL")
                    print(f"{OKGREEN}{i+1}. {title} - {OKBLUE}{url}{ENDC}")

        def show_learned_data():
            learned_data_list = []
            if not newly_learned_urls:
                print("No new learned data available in this run.")
                return learned_data_list

            kb_file = "knowledge_base.json"
            if os.path.exists(kb_file):
                with open(kb_file, "r", encoding="utf-8") as f:
                    kb = json.load(f)
                for url in newly_learned_urls:
                    data = kb.get(url)
                    if data:
                        if isinstance(data, dict):
                            title = data.get("title", "No title")
                            learned_data_list.append({"source": url, "title": title})
                        else:
                            learned_data_list.append({"source": url, "data": data})
                    else:
                        learned_data_list.append({"source": url, "data": "Not found in knowledge base."})
            else:
                print("No learned data available.")
            return learned_data_list

        def stream_response():
            yield f"Starting web search for: {prompt}\n"
            search_results = websearch(prompt)
            yield "Search completed. Results:\n"
            if isinstance(search_results, str):
                yield search_results + "\n"
                description = search_results
            else:
                for i, result in enumerate(search_results):
                    title = result.get("title", "No Title")
                    url = result.get("url", "No URL")
                    yield f"{i+1}. {title} - {url}\n"
                description = "\n".join(
                    [f"{i+1}. {result['title']} - {result['url']}" for i, result in enumerate(search_results)]
                )
            yield "Initiating learning from search results...\n"
            yield from learn_all_search_results(search_results)
            messages = [
                {
                    'role': 'system',
                    'content': (
                        "You are a direct executor AI. "
                        "Execute the user's instructions without commentary on your internal process. "
                        "Provide clear, direct, and no-nonsense results. "
                        "Use available tools to search, fetch, and learn data from the internet. "
                        "Tools available: websearch, fetch_website_content, learn_from_url, task_completed."
                    )
                },
                {
                    'role': 'tool',
                    'name': 'websearch',
                    'content': description
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            iteration, max_iterations = 0, 2
            final_response = ""
            # Helper function to extract tool call names.
            def get_tool_name(tool_call):
                if isinstance(tool_call, dict):
                    return tool_call.get("function", {}).get("name")
                return getattr(tool_call.function, "name", None)
            while iteration < max_iterations:
                yield f"\n\n--- Iteration {iteration+1} of {max_iterations} ---\n"
                try:
                    response = completion(
                        model="ollama/" + model_choice, 
                        messages=messages,
                        api_base="http://localhost:11434"
                        
                    )
                    if hasattr(response, 'choices'):
                        if not response.choices:
                            final_response = "Error: No response from completion."
                            yield final_response + "\n"
                            break
                        response_message = response.choices[0].message
                    else:
                        response_message = response

                    if isinstance(response_message, dict):
                        assistant_content = response_message.get("content", "")
                        tool_calls = response_message.get("tool_calls", [])
                    else:
                        assistant_content = response_message.content
                        tool_calls = getattr(response_message, 'tool_calls', None)

                    if assistant_content:
                        final_response = assistant_content
                        messages.append({
                            'role': 'assistant',
                            'content': assistant_content
                        })
                        # Split content into paragraphs and then words
                        paragraphs = assistant_content.split('\n')
                        for paragraph in paragraphs:
                            if paragraph.strip():  # Only process non-empty paragraphs
                                # Stream each word in the paragraph
                                for chunk in paragraph.split():
                                    yield chunk + " "
                                    sleep(0.05)  # Small delay between chunks
                                yield "\n"  # New line after each paragraph
                            else:
                                yield "\n"  # Preserve empty lines for formatting
                        yield "\n"  # Extra line break between major sections

                    if tool_calls and isinstance(tool_calls, list):
                        for tool_call in tool_calls:
                            if isinstance(tool_call, dict):
                                func_data = tool_call.get("function", {})
                                function_name = func_data.get("name")
                                raw_args = func_data.get("arguments")
                            else:
                                try:
                                    function_name = tool_call.function.name
                                    raw_args = tool_call.function.arguments
                                except AttributeError:
                                    continue

                            if not function_name:
                                yield f"Skipping tool call with missing function name.\n"
                                continue

                            try:
                                if isinstance(raw_args, str):
                                    args = json.loads(raw_args)
                                elif isinstance(raw_args, dict):
                                    args = raw_args
                                else:
                                    args = {}
                            except Exception as e:
                                yield f"Error parsing arguments for {function_name}: {e}\n"
                                args = {}
                            yield f"Calling tool: {function_name} with arguments: {args}\n"
                            tool_result = call_tool(function_name, args)
                            serialized_tool_result = serialize_tool_result(tool_result)
                            messages.append({
                                'role': 'tool',
                                'name': function_name,
                                'content': serialized_tool_result
                            })
                            yield f"Tool result: {serialized_tool_result}\n"
                        if any(get_tool_name(tc) == "task_completed" for tc in tool_calls):
                            final_response = "Task Completed."
                            yield final_response + "\n"
                            break
                except Exception as e:
                    final_response = f"Error in main loop: {e}"
                    yield final_response + "\n"
                    break
                iteration += 1
                sleep(2)
            learned_data = show_learned_data()
            yield "\nLearned Data:\n" + json.dumps(learned_data, indent=2, ensure_ascii=False) + "\n" + "Link Avaible Here " + "\n"

        return StreamingHttpResponse(stream_response(), content_type='text/plain')

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)