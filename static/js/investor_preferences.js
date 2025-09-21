// Investor Preferences page logic and API interactions

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('preferencesForm');
    const saveBtn = document.getElementById('savePreferencesBtn');
    
    if (!form) return;

    // Enhanced toast notification system
    const showToast = (message, type = 'success') => {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-xl shadow-lg transform transition-all duration-300 translate-x-full`;
        
        if (type === 'success') {
            toast.classList.add('bg-green-500/90', 'text-white', 'border', 'border-green-400/50');
        } else {
            toast.classList.add('bg-red-500/90', 'text-white', 'border', 'border-red-400/50');
        }
        
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                <span class="font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white/80 hover:text-white">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    };

    // AI Reranking Progress Popup
    const showRerankingProgress = () => {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4';
        overlay.id = 'rerankingProgressOverlay';
        
        // Track if process was cancelled
        let isCancelled = false;
        
        // Create popup
        const popup = document.createElement('div');
        popup.className = 'bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl transform transition-all duration-300 scale-95 opacity-0';
        
        popup.innerHTML = `
            <div class="text-center relative">
                <!-- Floating AI Particles -->
                <div class="ai-particles">
                    <div class="ai-particle" style="left: 20%; animation-delay: 0s;"></div>
                    <div class="ai-particle" style="left: 40%; animation-delay: 0.5s;"></div>
                    <div class="ai-particle" style="left: 60%; animation-delay: 1s;"></div>
                    <div class="ai-particle" style="left: 80%; animation-delay: 1.5s;"></div>
                </div>
                
                <!-- AI Brain Icon with Animation -->
                <div class="relative mb-6">
                    <div class="w-20 h-20 mx-auto bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center relative overflow-hidden ai-brain-icon">
                        <i class="fas fa-brain text-white text-2xl z-10"></i>
                        <!-- Pulsing ring animation -->
                        <div class="absolute inset-0 rounded-full border-4 border-blue-300 animate-ping"></div>
                        <div class="absolute inset-2 rounded-full border-2 border-purple-300 animate-pulse"></div>
                    </div>
                </div>
                
                <!-- Title -->
                <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    AI is Analyzing Your Preferences
                </h3>
                
                <!-- Subtitle -->
                <p class="text-gray-600 dark:text-gray-300 mb-6">
                    We're reranking startup opportunities based on your investment criteria
                </p>
                
                <!-- Progress Steps -->
                <div class="space-y-4 mb-6">
                    <div class="flex items-center space-x-3 text-left">
                        <div class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 progress-step completed">
                            <i class="fas fa-check text-white text-xs"></i>
                        </div>
                        <span class="text-sm text-gray-700 dark:text-gray-300 progress-step-text">Preferences saved successfully</span>
                    </div>
                    
                    <div class="flex items-center space-x-3 text-left">
                        <div class="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 progress-step active" data-step="analyzing">
                            <i class="fas fa-spinner fa-spin text-white text-xs"></i>
                        </div>
                        <span class="text-sm text-gray-700 dark:text-gray-300 progress-step-text">Analyzing startup profiles</span>
                    </div>
                    
                    <div class="flex items-center space-x-3 text-left">
                        <div class="w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 progress-step" data-step="ranking">
                            <i class="fas fa-clock text-white text-xs"></i>
                        </div>
                        <span class="text-sm text-gray-500 dark:text-gray-400 progress-step-text">Ranking opportunities</span>
                    </div>
                    
                    <div class="flex items-center space-x-3 text-left">
                        <div class="w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 progress-step" data-step="complete">
                            <i class="fas fa-clock text-white text-xs"></i>
                        </div>
                        <span class="text-sm text-gray-500 dark:text-gray-400 progress-step-text">Finalizing recommendations</span>
                    </div>
                </div>
                
                <!-- Progress Bar -->
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
                    <div class="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-1000 progress-bar" style="width: 25%"></div>
                </div>
                
                <!-- Status Text -->
                <p class="text-sm text-gray-500 dark:text-gray-400 progress-text">
                    This usually takes 10-15 seconds...
                </p>
                
                <!-- Close Button (optional) -->
                <div class="mt-6">
                    <button onclick="isCancelled = true; closeRerankingProgress(); setLoadingState(false);" class="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                        <i class="fas fa-times mr-1"></i>Cancel
                    </button>
                </div>
            </div>
        `;
        
        overlay.appendChild(popup);
        document.body.appendChild(overlay);
        
        // Animate in
        setTimeout(() => {
            popup.classList.remove('scale-95', 'opacity-0');
        }, 100);
        
        // Simulate progress steps
        const progressSteps = [
            { step: 'analyzing', delay: 2000, text: 'Analyzing startup profiles...' },
            { step: 'ranking', delay: 4000, text: 'Ranking opportunities by match score...' },
            { step: 'complete', delay: 6000, text: 'Finalizing your personalized recommendations...' }
        ];
        
        let currentStep = 0;
        const progressBar = popup.querySelector('.progress-bar');
        const progressText = popup.querySelector('.progress-text');
        
        const updateProgress = () => {
            // Check if process was cancelled
            if (isCancelled) {
                return;
            }
            
            if (currentStep < progressSteps.length) {
                const step = progressSteps[currentStep];
                
                // Update previous step to completed
                if (currentStep > 0) {
                    const prevStep = popup.querySelector(`[data-step="${progressSteps[currentStep - 1].step}"]`);
                    if (prevStep) {
                        prevStep.className = 'w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 progress-step completed';
                        prevStep.innerHTML = '<i class="fas fa-check text-white text-xs"></i>';
                        
                        // Update text color
                        const prevText = prevStep.parentElement.querySelector('.progress-step-text');
                        if (prevText) {
                            prevText.className = 'text-sm text-green-600 dark:text-green-400 progress-step-text';
                        }
                    }
                }
                
                // Update current step
                const currentStepEl = popup.querySelector(`[data-step="${step.step}"]`);
                if (currentStepEl) {
                    currentStepEl.className = 'w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 progress-step active';
                    currentStepEl.innerHTML = '<i class="fas fa-spinner fa-spin text-white text-xs"></i>';
                    
                    // Update text color
                    const currentText = currentStepEl.parentElement.querySelector('.progress-step-text');
                    if (currentText) {
                        currentText.className = 'text-sm text-blue-600 dark:text-blue-400 progress-step-text';
                    }
                }
                
                // Update progress bar
                const progress = ((currentStep + 1) / progressSteps.length) * 100;
                progressBar.style.width = `${progress}%`;
                
                // Update text
                progressText.textContent = step.text;
                
                currentStep++;
                
                if (currentStep < progressSteps.length) {
                    setTimeout(updateProgress, step.delay);
                } else {
                    // Complete all steps
                    setTimeout(() => {
                        // Check if process was cancelled
                        if (isCancelled) {
                            return;
                        }
                        
                        const allSteps = popup.querySelectorAll('.progress-step');
                        allSteps.forEach(stepEl => {
                            stepEl.className = 'w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 progress-step completed';
                            stepEl.innerHTML = '<i class="fas fa-check text-white text-xs"></i>';
                            
                            // Update text color
                            const stepText = stepEl.parentElement.querySelector('.progress-step-text');
                            if (stepText) {
                                stepText.className = 'text-sm text-green-600 dark:text-green-400 progress-step-text';
                            }
                        });
                        
                        progressBar.style.width = '100%';
                        progressText.textContent = 'Complete! Redirecting to your dashboard...';
                        
                        // Add completion animation
                        popup.classList.add('progress-complete');
                        
                        // Close popup and redirect after a short delay
                        setTimeout(() => {
                            if (!isCancelled) {
                                closeRerankingProgress();
                                window.location.href = '/investor/dashboard';
                            }
                        }, 1500);
                    }, 2000);
                }
            }
        };
        
        // Start progress after a very short delay
        setTimeout(updateProgress, 500);
        
        return overlay;
    };

    // Close reranking progress popup
    const closeRerankingProgress = () => {
        const overlay = document.getElementById('rerankingProgressOverlay');
        if (overlay) {
            const popup = overlay.querySelector('div');
            popup.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    };

    // Update progress popup for cached results
    const updateProgressForCachedResults = () => {
        const overlay = document.getElementById('rerankingProgressOverlay');
        if (!overlay) return;
        
        const popup = overlay.querySelector('div');
        const progressText = popup.querySelector('.progress-text');
        const progressBar = popup.querySelector('.progress-bar');
        
        // Update all steps to completed immediately
        const allSteps = popup.querySelectorAll('.progress-step');
        allSteps.forEach(stepEl => {
            stepEl.className = 'w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 progress-step completed';
            stepEl.innerHTML = '<i class="fas fa-check text-white text-xs"></i>';
            
            // Update text color
            const stepText = stepEl.parentElement.querySelector('.progress-step-text');
            if (stepText) {
                stepText.className = 'text-sm text-green-600 dark:text-green-400 progress-step-text';
            }
        });
        
        // Update progress bar to 100%
        progressBar.style.width = '100%';
        progressText.textContent = 'Using cached recommendations! Redirecting to your dashboard...';
        
        // Add completion animation
        popup.classList.add('progress-complete');
        
        // Close popup and redirect after a short delay
        setTimeout(() => {
            closeRerankingProgress();
            window.location.href = '/investor/dashboard';
        }, 1000);
    };

    // Make closeRerankingProgress globally available for error handling
    window.closeRerankingProgress = closeRerankingProgress;

    const apiUrl = '/investor/api/preferences';

    // Form validation
    const validateForm = () => {
        const errors = [];
        
        // Check if at least one sector is selected
        const sectors = form.querySelectorAll('input[name="sectors"]:checked');
        if (sectors.length === 0) {
            errors.push('Please select at least one sector');
        }
        
        // Check ticket size validation
        const ticketMin = parseFloat(form.querySelector('input[name="ticket_size_min"]').value);
        const ticketMax = parseFloat(form.querySelector('input[name="ticket_size_max"]').value);
        
        if (ticketMin && ticketMax && ticketMin > ticketMax) {
            errors.push('Minimum ticket size cannot be greater than maximum ticket size');
        }
        
        // Check if at least one investment stage is selected
        const stages = form.querySelectorAll('input[name="investment_stage"]:checked');
        if (stages.length === 0) {
            errors.push('Please select at least one investment stage');
        }
        
        return errors;
    };

    // Show validation errors
    const showValidationErrors = (errors) => {
        errors.forEach(error => {
            showToast(error, 'error');
        });
    };

    // Populate form with existing preferences
    const populateForm = (prefs) => {
        if (!prefs) return;
        
        form.querySelectorAll('input, select').forEach((el) => {
            const name = el.name;
            if (!name) return;
            
            if (Array.isArray(prefs[name])) {
                if (el.type === 'checkbox') {
                    el.checked = prefs[name].includes(el.value);
                }
            } else if (typeof prefs[name] !== 'undefined' && prefs[name] !== null) {
                el.value = prefs[name];
            }
        });
    };

    // Load existing preferences
    const loadPreferences = async () => {
        try {
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            if (data.success) {
                populateForm(data.data);
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    };

    // Collect and validate form data
    const collectFormData = () => {
        const formData = new FormData(form);
        const payload = {};

        // Handle checkbox groups (multi-select)
        const listFields = ['sectors', 'investment_stage', 'geography', 'business_model', 'funding_types'];
        listFields.forEach((field) => {
            const values = formData.getAll(field);
            if (values && values.length) payload[field] = values;
        });

        // Handle numeric fields
        const ticketMin = formData.get('ticket_size_min');
        const ticketMax = formData.get('ticket_size_max');
        const exitTimeline = formData.get('exit_timeline');
        const investmentsPerYear = formData.get('number_of_investments_per_year');
        
        if (ticketMin) payload['ticket_size_min'] = parseFloat(ticketMin);
        if (ticketMax) payload['ticket_size_max'] = parseFloat(ticketMax);
        if (exitTimeline) payload['exit_timeline'] = parseInt(exitTimeline);
        if (investmentsPerYear) payload['number_of_investments_per_year'] = parseInt(investmentsPerYear);
        
        // Handle select fields
        const riskTolerance = formData.get('risk_tolerance');
        const involvementLevel = formData.get('involvement_level');
        
        if (riskTolerance) payload['risk_tolerance'] = riskTolerance;
        if (involvementLevel) payload['involvement_level'] = involvementLevel;

        return payload;
    };

    // Set loading state
    const setLoadingState = (loading) => {
        if (loading) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
            saveBtn.classList.add('opacity-75', 'cursor-not-allowed');
        } else {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Save Preferences';
            saveBtn.classList.remove('opacity-75', 'cursor-not-allowed');
        }
    };

    // Form submission handler
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Validate form
        const validationErrors = validateForm();
        if (validationErrors.length > 0) {
            showValidationErrors(validationErrors);
            return;
        }
        
        const payload = collectFormData();
        
        // Show the AI reranking progress popup immediately
        const progressOverlay = showRerankingProgress();
        
        // Disable the form to prevent multiple submissions
        setLoadingState(true);

        try {
            const response = await fetch(apiUrl, {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload),
            });
            
               const data = await response.json();
               
               if (data.success) {
                   // Preferences saved successfully - check if cached results were used
                   if (data.cached) {
                       console.log('Preferences saved successfully, using cached recommendations...');
                       // Update popup to show cached results message
                       updateProgressForCachedResults();
                   } else {
                       console.log('Preferences saved successfully, AI reranking in progress...');
                   }
               } else {
                   // Close popup and show error
                   closeRerankingProgress();
                   showToast(data.message || 'Failed to save preferences', 'error');
                   setLoadingState(false);
               }
        } catch (error) {
            console.error('Error saving preferences:', error);
            // Close popup and show error
            closeRerankingProgress();
            showToast('Network error. Please try again.', 'error');
            setLoadingState(false);
        }
    });

    // Real-time validation for ticket sizes
    const ticketMinInput = form.querySelector('input[name="ticket_size_min"]');
    const ticketMaxInput = form.querySelector('input[name="ticket_size_max"]');
    
    const validateTicketSizes = () => {
        const min = parseFloat(ticketMinInput.value);
        const max = parseFloat(ticketMaxInput.value);
        
        if (min && max && min > max) {
            ticketMinInput.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
            ticketMaxInput.classList.add('border-red-500', 'ring-2', 'ring-red-500/20');
        } else {
            ticketMinInput.classList.remove('border-red-500', 'ring-2', 'ring-red-500/20');
            ticketMaxInput.classList.remove('border-red-500', 'ring-2', 'ring-red-500/20');
        }
    };
    
    if (ticketMinInput) ticketMinInput.addEventListener('input', validateTicketSizes);
    if (ticketMaxInput) ticketMaxInput.addEventListener('input', validateTicketSizes);

    // Initialize - load preferences on page load
    loadPreferences();
});
