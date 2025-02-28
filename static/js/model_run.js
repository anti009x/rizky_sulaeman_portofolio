let currentGroup = 1;
    function cycleButtons() {
        const totalGroups = 3;
        // Hide current group
        document.querySelector('[data-group="' + currentGroup + '"]').classList.add('hidden');
        // Move to next group (cycle back to 1 after the last group)
        currentGroup = currentGroup === totalGroups ? 1 : currentGroup + 1;
        // Show the next group
        document.querySelector('[data-group="' + currentGroup + '"]').classList.remove('hidden');
    }



  document.addEventListener('DOMContentLoaded', function() {
    // Event delegation on the container holding your button groups
    const buttonGroups = document.getElementById('button-groups');

    buttonGroups.addEventListener('click', function(e) {
      // Find the closest button (if clicking on an inner element)
      const clickedBtn = e.target.closest('button');
      if (!clickedBtn) return;  // Exit if not clicking on a button

      // Get the parent group that is currently visible
      const visibleGroup = clickedBtn.closest('.button-group:not(.hidden)');
      if (!visibleGroup) return;

      // If the clicked button is already active, reset all buttons to original size
      if (clickedBtn.classList.contains('active')) {
        visibleGroup.querySelectorAll('button').forEach(function(btn) {
          btn.classList.remove('active', 'inactive');
        });
        return;
      }

      // Otherwise, remove any existing active/inactive classes
      visibleGroup.querySelectorAll('button').forEach(function(btn) {
        btn.classList.remove('active', 'inactive');
      });

      // Mark the clicked button as "active"
      clickedBtn.classList.add('active');

      // Mark all other buttons in the same group as "inactive" (i.e. shrink them)
      visibleGroup.querySelectorAll('button').forEach(function(btn) {
        if (btn !== clickedBtn) {
          btn.classList.add('inactive');
        }
      });
    });
  });

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
      

    });

    // Hide the dropdown when clicking outside
    $(document).on('click', function() {
      $optionsContainer.addClass('hidden');
    });
  });

// Chat functionality
