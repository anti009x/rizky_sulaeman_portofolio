function getNewResponseContainer() {
  const template = document.getElementById('ai_response-template');
  const clone = template.content.cloneNode(true);
  const conversationWrapper = document.getElementById('conversation-wrapper');
  conversationWrapper.appendChild(clone);
  const newResponse = conversationWrapper.lastElementChild;
  return newResponse.querySelector('.ai_message-text');
}

const button_web_search = document.getElementById('web-search-btn');
let webSearchEnabled = false;

function getUserMessage() {
  const template = document.getElementById('response-template_user');
  const clone = template.content.cloneNode(true);
  const conversationWrapper = document.getElementById('conversation-wrapper');
  conversationWrapper.appendChild(clone);
  const newUserMessage = conversationWrapper.lastElementChild;
  return newUserMessage.querySelector('.user-message');
}

document.addEventListener('DOMContentLoaded', function() {
  const chatInput = document.getElementById('chat-input');
  const submitButton = chatInput ? chatInput.nextElementSibling : null;
  const modelSelect = document.getElementById('model-select');
  const fileInput = document.getElementById('file_input');
  const editButton = document.getElementById('edit-button');
  const sendEditButton = editButton ? editButton.nextElementSibling : null;

  function handleCombinedSubmit() {
      const message = chatInput.value.trim();
      if (!message) return;

      const selectedModel = modelSelect.value;
      if (!selectedModel || selectedModel === "Select") {
          alert("Please manually select a model before sending a message");
          return;
      }

      // Create FormData object to handle file uploads
      const formData = new FormData();
      formData.append('message', message);
      formData.append('model', selectedModel);

      // Check for a file in the fileInput and append it to the FormData.
      // Also, grab the file's name to display in the user message.
      let fileAttached = false;
      let attachedFileName = "";
      let fileUrl = "";
      if (fileInput && fileInput.files.length > 0) {
          const file = fileInput.files[0];
          formData.append('file', file);
          fileAttached = true;
          attachedFileName = file.name;
          fileUrl = URL.createObjectURL(file);
      }

      // Clear the chat input after reading its content.
      chatInput.value = '';

      // Get the user message DOM element from the template.
      const userMessageElement = getUserMessage();
      if (userMessageElement) {
          let displayText = message;
          if (fileAttached) {
              const fileLink = document.createElement('a');
              fileLink.href = fileUrl;
              fileLink.download = attachedFileName;
              fileLink.textContent = attachedFileName;
              fileLink.style.color = 'white';
              fileLink.style.textDecoration = 'underline';
              
              userMessageElement.textContent = displayText + " (File attached: ";
              userMessageElement.appendChild(fileLink);
              userMessageElement.appendChild(document.createTextNode(")"));
          } else {
              userMessageElement.textContent = displayText;
          }
          userMessageElement.closest('.response-container-user').style.display = 'flex';
      }

      if (!webSearchEnabled) {
          const targetElementNormal = getNewResponseContainer();
          fetch('/send_message/', {
                  method: 'POST',
                  headers: {
                      'X-CSRFToken': getCookie('csrftoken')
                  },
                  body: formData
              })
              .then(response => {
                  if (!response.ok) {
                      throw new Error('Selected model not found or unavailable. Please choose another model.');
                  }
                  const reader = response.body.getReader();
                  const decoder = new TextDecoder('utf-8');

                  function read() {
                      return reader.read().then(({ done, value }) => {
                          if (done) {
                              chatInput.style.height = 'auto';
                              return;
                          }
                          let text = decoder.decode(value, { stream: true });
                          if (targetElementNormal) {
                              targetElementNormal.textContent += text;
                              targetElementNormal.closest('.ai_response-container').style.display = 'flex';
                          }
                          return read();
                      });
                  }
                  return read();
              })
              .catch(error => {
                  console.error('Error:', error);
                  alert('Error: ' + error.message + '\nPlease select a different model and try again.');
              });
      } else {
          const targetElementWebSearch = getNewResponseContainer();
          fetch('/send_message_web_search/', {
                  method: 'POST',
                  headers: {
                      'X-CSRFToken': getCookie('csrftoken')
                  },
                  body: formData
              })
              .then(final_response => {
                  if (!final_response.ok) {
                      throw new Error('Selected model not found or unavailable. Please choose another model.');
                  }
                  const reader = final_response.body.getReader();
                  const decoder = new TextDecoder('utf-8');

                  function read() {
                      return reader.read().then(({ done, value }) => {
                          if (done) {
                              chatInput.style.height = 'auto';
                              const accumulatedText = targetElementWebSearch.textContent;
                              const linkRegex = /(https:\/\/[^\s]+)/g;
                              const matches = [...accumulatedText.matchAll(linkRegex)];
                              if (matches.length > 0) {
                                  const cleanedText = accumulatedText.replace(linkRegex, '');
                                  targetElementWebSearch.textContent = cleanedText;
                                  const textElements = document.querySelectorAll('.ai_message-text');

                                  const uniqueLinks = new Set(matches.map(match => match[0]));
                                  textElements.forEach(el => {
                                      uniqueLinks.forEach(link => {
                                          try {
                                              if (!el.querySelector(`a[href="${link}"]`)) {
                                                  const a = document.createElement('a');
                                                  a.href = link;
                                                  a.textContent = link;
                                                  a.target = '_blank';
                                                  el.appendChild(a);
                                                  el.appendChild(document.createElement('br'));
                                              }
                                          } catch (error) {
                                              console.error('Error:', error);
                                          };
                                      });
                                  });
                              }
                              return;
                          }
                          let text = decoder.decode(value, { stream: true });
                          if (targetElementWebSearch) {
                              targetElementWebSearch.textContent += text;
                              targetElementWebSearch.closest('.ai_response-container').style.display = 'flex';
                          }
                          return read();
                      });
                  }
                  return read();
              })
              .catch(error => {
                  console.error('Error:', error);
                  alert('Error: ' + error.message + '\nPlease select a different model and try again.');
              });
      }
  }

  if (button_web_search) {
      button_web_search.addEventListener('click', function() {
          console.log('Web search button clicked');
          webSearchEnabled = !webSearchEnabled;

          if (!webSearchEnabled) {
              this.style.backgroundColor = '';
          } else {
              this.style.backgroundColor = '#3b82f6';
          }
      });
  } else {
      console.warn('Web search button (web-search-btn) not found.');
  }

  function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }

  if (submitButton) {
      submitButton.addEventListener('click', handleCombinedSubmit);
  }

  if (chatInput) {
      chatInput.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleCombinedSubmit();
          }
      });
  }

  if (sendEditButton) {
      sendEditButton.addEventListener('click', function() {
          if (!webSearchEnabled) {
              handleCombinedSubmit();
          } else {
              if (button_web_search) {
                  handleCombinedSubmit();
              } else {
                  console.warn('Web search button not found, cannot submit with web search enabled');
                  return;
              }
          }
      });
  }

  if (editButton) {
      editButton.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (!webSearchEnabled) {
                  handleCombinedSubmit();
              } else {
                  if (button_web_search) {
                      handleCombinedSubmit();
                  } else {
                      console.warn('Web search button not found, cannot submit with web search enabled');
                      return;
                  }
              }
          }
      });
  }
});