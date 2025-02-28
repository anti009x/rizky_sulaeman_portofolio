$(document).ready(function() {
    var $customSelect = $('.custom-select');
    var $select = $customSelect.find('select');
    var $display = $customSelect.find('.select-display');
    var $optionsContainer = $customSelect.find('.custom-options');

    // Style each option (for the jQuery-built list) using Tailwind classes
    $select.find('option').addClass('bg-gray-800 text-white');

    // Build the custom options list from the select's options
    $select.find('option').each(function() {
      var $option = $(this);
      if (!$option.val()) return;
      var $optionElement = $('<div class="flex items-center px-4 py-2 bg-gray-800 text-white cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"></div>');
      var $img = $('<img>', {
        src: $option.data('img'),
        class: 'w-5 h-5 mr-2',
        alt: ''
      });
      var $text = $('<span class="text-[10px]">' + $option.text() + '</span>');
      $optionElement.append($img).append($text);
      $optionsContainer.append($optionElement);

      // When a custom option is clicked, update the hidden select and the display text, then hide the dropdown
      $optionElement.on('click', function() {
        $select.val($option.val());
        $display.find('.selected-option').text($option.text());
        $optionsContainer.addClass('hidden');
      });
    });

    // Toggle the custom dropdown when clicking on the display element
    $display.on('click', function(e) {
      e.stopPropagation();
      $optionsContainer.toggleClass('hidden');
      
      // Force the dropdown to appear below the button by setting top to 100%
      if (!$optionsContainer.hasClass('hidden')) {
        var buttonHeight = $display.outerHeight();
        $optionsContainer.css({
          'bottom': buttonHeight + 'px',
          'top': 'auto',
          'left': '0',
          'position': 'absolute'
        });
      }
    });

    // Hide the dropdown when clicking outside
    $(document).on('click', function() {
      $optionsContainer.addClass('hidden');
    });
}); 