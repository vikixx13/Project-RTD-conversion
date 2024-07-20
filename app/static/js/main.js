// static/js/main.js


document.addEventListener('DOMContentLoaded', function() {
    var methodSelect = document.getElementById('method');
    var fileInput = document.getElementById('file_input');
    var singleValueInput = document.getElementById('single_value_input');

    methodSelect.addEventListener('change', function() {
        if (this.value === 'single_value_conversion') {
            fileInput.style.display = 'none';
            singleValueInput.style.display = 'block';
        } else {
            fileInput.style.display = 'block';
            singleValueInput.style.display = 'none';
        }
    });
});
