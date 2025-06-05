(function() {
    const cardGrid = document.getElementById('cardGrid');
    const syllabiDataPath = 'data/syllabi.json';
    const searchBar = document.getElementById('search-bar');
    const filterPanel = document.getElementById('filter-panel'); // Added filterPanel
    const mobileFilterToggleButton = document.getElementById('mobile-filter-toggle'); // Added mobile toggle button

    let allSyllabi = [];
    let currentlyDisplayedSyllabi = [];
    let activeFilters = { // Object to store active filters
        term: [],
        level: [], // Course level (e.g., 100, 200)
        tags: []
    };
    let currentSearchTerm = ''; // Store current search term

    // Function to create a single syllabus card element
    function createSyllabusCard(syllabus) {
        const card = document.createElement('div');
        card.className = 'p-4 rounded-card shadow-md card-animate-in';
        card.style.backgroundColor = 'var(--bg-alt)';
        card.style.border = '1px solid var(--accent1)';
        card.style.borderRadius = '0.5rem';

        card.addEventListener('mouseenter', () => card.classList.add('scanline-active'));
        card.addEventListener('mouseleave', () => card.classList.remove('scanline-active'));

        const header = document.createElement('h3');
        header.className = 'text-xl font-secondary mb-2';
        header.style.color = 'var(--accent1)';
        header.textContent = `${syllabus.courseCode}: ${syllabus.title}`;
        card.appendChild(header);

        const subtext = document.createElement('p');
        subtext.className = 'text-sm font-primary mb-1';
        subtext.style.color = 'var(--fg)';
        subtext.textContent = `Term: ${syllabus.term} | Instructor: ${syllabus.instructor}`;
        card.appendChild(subtext);

        const description = document.createElement('p');
        description.className = 'text-sm font-primary mb-3';
        description.style.color = 'var(--fg)';
        description.textContent = syllabus.description;
        card.appendChild(description);

        if (syllabus.tags && syllabus.tags.length > 0) {
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'mb-3 flex flex-wrap gap-2 tags-container';
            syllabus.tags.forEach(tagText => {
                const tag = document.createElement('span');
                tag.className = 'text-xs font-primary px-2 py-1 rounded-full';
                tag.style.backgroundColor = 'var(--accent2)';
                tag.style.color = 'var(--bg)';
                tag.textContent = tagText;
                tagsContainer.appendChild(tag);
            });
            card.appendChild(tagsContainer);
        }

        const downloadButton = document.createElement('button');
        downloadButton.className = 'w-full font-secondary py-2 px-4 rounded focus:outline-none';
        downloadButton.textContent = syllabus.fileFormats && syllabus.fileFormats.length > 1 ? 'DOWNLOAD OPTIONS' : 'DOWNLOAD';
        downloadButton.setAttribute('data-course-code', syllabus.courseCode);
        card.appendChild(downloadButton);

        return card;
    }

    // Function to render syllabus cards to the grid
    function renderSyllabusCards(syllabiToRender) {
        if (!cardGrid) {
            console.error('Error: cardGrid element not found.');
            return;
        }
        cardGrid.innerHTML = '';

        if (syllabiToRender.length === 0) {
            cardGrid.innerHTML = '<p class="text-center col-span-full" style="color: var(--fg);">No syllabi found matching your criteria.</p>';
            return;
        }

        syllabiToRender.forEach((syllabus, index) => {
            const cardElement = createSyllabusCard(syllabus);
            cardElement.style.animationDelay = `${index * 50}ms`;
            cardGrid.appendChild(cardElement);
        });
    }

    // --- Combined Filtering Logic (Search and Checkbox Filters) ---
    function applyAllFilters() {
        let filtered = [...allSyllabi];

        // Apply search term filter first
        const lowerCaseSearchTerm = currentSearchTerm.toLowerCase().trim();
        if (lowerCaseSearchTerm) {
            filtered = filtered.filter(syllabus => {
                return (
                    syllabus.courseCode.toLowerCase().includes(lowerCaseSearchTerm) ||
                    syllabus.title.toLowerCase().includes(lowerCaseSearchTerm) ||
                    syllabus.instructor.toLowerCase().includes(lowerCaseSearchTerm) ||
                    (syllabus.tags && syllabus.tags.some(tag => tag.toLowerCase().includes(lowerCaseSearchTerm)))
                );
            });
        }

        // Apply checkbox filters
        // Term filter
        if (activeFilters.term.length > 0) {
            filtered = filtered.filter(syllabus => activeFilters.term.includes(syllabus.term));
        }
        // Level filter (extract starting digit for level)
        if (activeFilters.level.length > 0) {
            filtered = filtered.filter(syllabus => {
                const courseLevelPrefix = syllabus.courseCode.match(/^\D*(\d)/); // Extracts the first digit(s) after any non-digits
                if (courseLevelPrefix && courseLevelPrefix[1]) {
                     // Check if any active level filter matches the first digit of the course code (e.g., '1' for 100-level)
                    return activeFilters.level.some(levelFilter => courseLevelPrefix[1].startsWith(levelFilter.charAt(0)));
                }
                return false;
            });
        }
        // Tags filter (match any selected tag)
        if (activeFilters.tags.length > 0) {
            filtered = filtered.filter(syllabus =>
                syllabus.tags && syllabus.tags.some(tag => activeFilters.tags.includes(tag))
            );
        }

        currentlyDisplayedSyllabi = filtered;
        renderSyllabusCards(currentlyDisplayedSyllabi);
    }

    // --- Search Functionality ---
    if (searchBar) {
        searchBar.addEventListener('input', (event) => {
            currentSearchTerm = event.target.value;
            applyAllFilters(); // Use combined filter function
        });
    }

    // --- Filter Panel Functionality ---
    if (filterPanel) {
        const checkboxes = filterPanel.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (event) => {
                const filterGroup = event.target.dataset.filterGroup;
                const filterValue = event.target.value;

                if (filterGroup) {
                    if (event.target.checked) {
                        if (!activeFilters[filterGroup].includes(filterValue)) {
                            activeFilters[filterGroup].push(filterValue);
                        }
                    } else {
                        activeFilters[filterGroup] = activeFilters[filterGroup].filter(item => item !== filterValue);
                    }
                    applyAllFilters(); // Use combined filter function
                }
            });
        });
    }

    // Mobile Filter Panel Toggle
    if (mobileFilterToggleButton && filterPanel) {
        // Hide panel by default on mobile if it's not already styled by Tailwind for that
        // filterPanel.classList.add('hidden'); // Or use Tailwind's `md:block` etc.

        mobileFilterToggleButton.addEventListener('click', () => {
            // Assuming the filter panel's main content div is the first child or has a specific ID/class
            const filterContent = filterPanel.querySelector('div'); // Adjust if structure is different
            if (filterContent) {
                 filterContent.classList.toggle('hidden'); // Toggle visibility of content
                 // Or toggle a class on filterPanel itself if it controls padding/border
            }
            // Change button text
            if (filterContent && filterContent.classList.contains('hidden')) {
                mobileFilterToggleButton.textContent = 'Show Filters';
            } else {
                mobileFilterToggleButton.textContent = 'Hide Filters';
            }
        });
        // Initial state for mobile: hide filters if screen is small
        // This is better handled by Tailwind's responsive classes (e.g. hidden md:block for filterContent)
        // For JS solution:
        // if (window.innerWidth < 768) { // md breakpoint
        //    const filterContent = filterPanel.querySelector('div');
        //    if (filterContent) filterContent.classList.add('hidden');
        //    mobileFilterToggleButton.textContent = 'Show Filters';
        // }
    }


    // Function to fetch syllabus data
    async function fetchSyllabi() {
        try {
            const response = await fetch(syllabiDataPath);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            allSyllabi = await response.json();
            // Initialize activeFilters with available options from data (optional, but good for dynamic filters)
            // For now, filters are static in HTML.

            currentlyDisplayedSyllabi = [...allSyllabi];
            applyAllFilters(); // Apply any default or persisted filters on load
            console.log('Syllabi data loaded and initial filters applied.');
        } catch (error) {
            console.error('Error fetching syllabi data:', error);
            if (cardGrid) {
                cardGrid.innerHTML = '<p class="text-center col-span-full" style="color: var(--fg);">Error loading syllabi data. Please try again later.</p>';
            }
        }
    }

    fetchSyllabi();

    window.syllabusApp = {
        allSyllabi: () => allSyllabi,
        currentlyDisplayedSyllabi: () => currentlyDisplayedSyllabi,
        activeFilters: () => activeFilters,
        renderSyllabusCards,
        applyAllFilters
    };

})();
