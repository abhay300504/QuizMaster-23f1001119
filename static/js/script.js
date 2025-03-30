// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Timer functionality for quiz page
    const timerElement = document.getElementById('time-display');
    const quizForm = document.getElementById('quiz-form');
    
    if (timerElement && quizForm) {
        const timerContainer = document.getElementById('timer');
        
        // Extract initial time from the page or default to 0
        let timeString = timerElement.textContent;
        let [initialMinutes, initialSeconds] = timeString.split(':').map(num => parseInt(num, 10) || 0);
        
        // Fallback if time parsing fails
        if (isNaN(initialMinutes)) {
            initialMinutes = 0;
        }
        if (isNaN(initialSeconds)) {
            initialSeconds = 0;
        }
        
        // Calculate total seconds
        let totalSeconds = (initialMinutes * 60) + initialSeconds;
        
        // Only start timer if we have a valid duration
        if (totalSeconds > 0) {
            const countdown = setInterval(function() {
                // Decrement total seconds
                totalSeconds--;
                
                // Stop if time is up
                if (totalSeconds <= 0) {
                    clearInterval(countdown);
                    alert('Time is up! Your quiz will be submitted automatically.');
                    quizForm.submit();
                    return;
                }
                
                // Change color when less than 1 minute remains
                if (totalSeconds < 60 && timerContainer) {
                    timerContainer.classList.remove('alert-warning');
                    timerContainer.classList.add('alert-danger');
                }
                
                // Calculate minutes and seconds
                const minutes = Math.floor(totalSeconds / 60);
                const seconds = totalSeconds % 60;
                
                // Update timer display
                if (timerElement) {
                    timerElement.textContent = 
                        minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
                }
            }, 1000);
        } else {
            console.warn('Invalid quiz duration. Timer not started.');
            if (timerElement) {
                timerElement.textContent = 'Timer Error';
            }
        }
    }

    // Existing functionality for saving and loading quiz progress
    const quizId = quizForm ? quizForm.querySelector('input[name="quiz_id"]')?.value : null;
    
    if (quizId) {
        // Load previously saved progress
        const savedAnswers = JSON.parse(localStorage.getItem(`quiz_${quizId}_progress`) || '{}');
        
        // Restore saved answers
        for (const [questionId, answer] of Object.entries(savedAnswers)) {
            const radioButton = document.querySelector(`input[name="answer_${questionId}"][value="${answer}"]`);
            if (radioButton) {
                radioButton.checked = true;
            }
        }
        
        // Save progress when answers change
        const radioButtons = document.querySelectorAll('input[type="radio"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                const answers = JSON.parse(localStorage.getItem(`quiz_${quizId}_progress`) || '{}');
                const questionId = this.name.split('_')[1];
                answers[questionId] = this.value;
                localStorage.setItem(`quiz_${quizId}_progress`, JSON.stringify(answers));
            });
        });
        
        // Clear saved progress on form submission
        quizForm.addEventListener('submit', function() {
            localStorage.removeItem(`quiz_${quizId}_progress`);
        });
    }
});
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Tooltips initialization
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Search box filter functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const items = document.querySelectorAll('.searchable-item');
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(filter)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Show the active quiz question on mobile
    const questionLinks = document.querySelectorAll('.question-nav-link');
    questionLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            questionLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all questions
            const questions = document.querySelectorAll('.question-container');
            questions.forEach(q => q.classList.add('d-none'));
            
            // Show the selected question
            const targetId = this.getAttribute('href').slice(1);
            document.getElementById(targetId).classList.remove('d-none');
        });
    });
    

// Function to handle chart creation
function createChart(canvasId, type, labels, datasets) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Function to save quiz progress to local storage
function saveQuizProgress(quizId) {
    const form = document.getElementById('quiz-form');
    if (!form) return;
    
    const answers = {};
    const radioGroups = form.querySelectorAll('input[type="radio"]:checked');
    
    radioGroups.forEach(radio => {
        const name = radio.getAttribute('name');
        const questionId = name.split('_')[1];
        answers[questionId] = radio.value;
    });
    
    localStorage.setItem(`quiz_${quizId}_progress`, JSON.stringify(answers));
}

// Function to load quiz progress from local storage
function loadQuizProgress(quizId) {
    const saved = localStorage.getItem(`quiz_${quizId}_progress`);
    if (!saved) return;
    
    const answers = JSON.parse(saved);
    
    for (const questionId in answers) {
        const selector = `input[name="answer_${questionId}"][value="${answers[questionId]}"]`;
        const radio = document.querySelector(selector);
        if (radio) {
            radio.checked = true;
        }
    }
}