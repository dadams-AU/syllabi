(function() {
    const cardGrid = document.getElementById('cardGrid');
    const syllabiDataPath = 'data/syllabi.json';
    const searchBar = document.getElementById('search-bar');
    const filterPanel = document.getElementById('filter-panel'); // Added filterPanel
    const sortDropdown = document.getElementById("sort-dropdown"); // Added for sorting
    const mobileFilterToggleButton = document.getElementById('mobile-filter-toggle'); // Added mobile toggle button
    const termFiltersContainer = document.getElementById("term-filters-container");
    const levelFiltersContainer = document.getElementById("level-filters-container");
    const tagFiltersContainer = document.getElementById("tag-filters-container");

    let allSyllabi = [];
    let currentlyDisplayedSyllabi = [];
    let activeFilters = { // Object to store active filters
        term: [],
        year: [],
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
        subtext.textContent = `Term: ${syllabus.term}`;
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

        const downloadLink = document.createElement("a");
        downloadLink.className = "retro-button block w-full text-center font-secondary py-2 px-4 rounded focus:outline-none"; // Added retro-button class
        downloadLink.style.textDecoration = "none";
        downloadLink.href = syllabus.path; // Path from syllabi.json
        let buttonText = "DOWNLOAD PDF";
        // syllabus.fileFormats might contain ["PDF", "TEX"]
        // For now, syllabus.path directly points to the PDF version from the JSON generation step.
        // If TEX is primary or choice is needed, JSON structure or this logic needs adjustment.
        downloadLink.textContent = buttonText;
        downloadLink.setAttribute("download", syllabus.path.split("/").pop()); // Set download attribute with filename
        card.appendChild(downloadLink);

        return card;
    }

    // Function to render syllabus cards to the grid

    // --- Helper function for sorting by term ---
    function termToComparable(termStr) {
        if (!termStr || typeof termStr !== "string") return 0;
        const parts = termStr.toLowerCase().split(" ");
        let year, seasonOrder;

        // Handle "YYYY-YY Season" like "2023-24 Intersession" -> treat as start year (2023)
        const yearRangeMatch = termStr.match(/(\d{4})-\d{2}/);
        if (yearRangeMatch) {
            year = parseInt(yearRangeMatch[1]);
        } else {
            // Find year part (e.g., 2024, 2025)
            const yearPart = parts.find(p => /^\d{4}$/.test(p));
            year = yearPart ? parseInt(yearPart) : 0;
        }

        // Determine season order (higher number = later in year)
        if (termStr.toLowerCase().includes("spring")) seasonOrder = 1;
        else if (termStr.toLowerCase().includes("summer")) seasonOrder = 2;
        else if (termStr.toLowerCase().includes("fall")) seasonOrder = 3;
        else if (termStr.toLowerCase().includes("intersession") || termStr.toLowerCase().includes("winter")) seasonOrder = 0; // Winter/Intersession before Spring
        else seasonOrder = 0; // Default for unknown terms

        return year * 10 + seasonOrder; // e.g., Fall 2024 -> 20243, Spring 2025 -> 20251
    }

    // --- Dynamic Filter Population ---
    function populateDynamicFilters(syllabi) {
        // Check yearFiltersContainer instead of tagFiltersContainer
        const yearFiltersContainer = document.getElementById("year-filters-container");
        if (!termFiltersContainer || !levelFiltersContainer || !yearFiltersContainer) {
            console.error("Filter container elements not found!");
            return;
        }

        const terms = [...new Set(syllabi.map(s => s.term).filter(t => t && t !== "Undated"))].sort();
        const years = [...new Set(syllabi.map(s => s.year).filter(y => y))].sort((a, b) => b - a);
        const levels = [...new Set(syllabi.map(s => {
            const code = s.courseCode || "";
            const match = code.match(/^\D*(\d)/); // Match first digit after optional non-digits
            return match ? `${match[1]}00-level` : null; // e.g. POSC 315 -> 300-level
        }))].filter(l => l).sort((a,b) => parseInt(a) - parseInt(b)); // Sort numerically
        const tags = [...new Set(syllabi.flatMap(s => s.tags || []).filter(t => t))].sort();

        const createCheckbox = (group, value, labelText) => {
            const label = document.createElement("label");
            label.className = "flex items-center space-x-2 font-primary text-sm py-1";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.className = "form-checkbox h-4 w-4";
            input.dataset.filterGroup = group;
            input.value = value;
            label.appendChild(input);
            const span = document.createElement("span");
            span.textContent = labelText;
            label.appendChild(span);
            return label;
        };

        termFiltersContainer.innerHTML = "";
        // Insert year filters after clearing term container
        if (yearFiltersContainer) {
            yearFiltersContainer.innerHTML = "";
            years.forEach(year => yearFiltersContainer.appendChild(createCheckbox("year", year, year)));
        }
        terms.forEach(term => termFiltersContainer.appendChild(createCheckbox("term", term, term)));

        levelFiltersContainer.innerHTML = "";
        // For levels, the value is "100", "200", etc. Label is "100-level"
        levels.forEach(levelFullText => levelFiltersContainer.appendChild(createCheckbox("level", levelFullText.substring(0,3), levelFullText)));

        if (tagFiltersContainer) { // Only populate tags if the container exists
            tagFiltersContainer.innerHTML = "";
            tags.forEach(tag => tagFiltersContainer.appendChild(createCheckbox("tags", tag, tag)));
        }
    }

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

    // --- Sorting Functionality ---
    function sortSyllabi(syllabiArray, sortByValue) {
        const sortedArray = [...syllabiArray]; // Work on a copy

        switch (sortByValue) {
            case "newest":
                sortedArray.sort((a, b) => termToComparable(b.term) - termToComparable(a.term));
                break;
            case "oldest":
                sortedArray.sort((a, b) => termToComparable(a.term) - termToComparable(b.term));
                break;
            case "code_asc":
                sortedArray.sort((a, b) => a.courseCode.localeCompare(b.courseCode));
                break;
            // Add Z-A for course code if needed, requires new option in HTML
            // case "code_desc":
            //    sortedArray.sort((a, b) => b.courseCode.localeCompare(a.courseCode));
            //    break;
            default:
                // Default sort or no sort if value is unknown
                break;
        }
        return sortedArray;
    }

    function applyAllFilters() {
        let filtered = [...allSyllabi];

        // Apply search term filter first
        const lowerCaseSearchTerm = currentSearchTerm.toLowerCase().trim();
        if (lowerCaseSearchTerm) {
            filtered = filtered.filter(syllabus => {
                return (
                    syllabus.courseCode.toLowerCase().includes(lowerCaseSearchTerm) ||
                    syllabus.title.toLowerCase().includes(lowerCaseSearchTerm) ||
                    (syllabus.tags && syllabus.tags.some(tag => tag.toLowerCase().includes(lowerCaseSearchTerm)))
                );
            });
        }

        // Apply checkbox filters
        // Term filter
        if (activeFilters.term.length > 0) {
            filtered = filtered.filter(syllabus => activeFilters.term.includes(syllabus.term));
        }
        // Year filter
        if (activeFilters.year.length > 0) {
            filtered = filtered.filter(syllabus => activeFilters.year.includes(syllabus.year));
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
        if (sortDropdown && sortDropdown.value) {
            currentlyDisplayedSyllabi = sortSyllabi(currentlyDisplayedSyllabi, sortDropdown.value);
        }
        renderSyllabusCards(currentlyDisplayedSyllabi);
    }

    // --- Search Functionality ---
    if (searchBar) {
        searchBar.addEventListener('input', (event) => {
            currentSearchTerm = event.target.value;
            applyAllFilters(); // Use combined filter function
        });
    }

    // --- Filter Panel Functionality (Event Delegation) ---
    if (filterPanel) {
        filterPanel.addEventListener("change", (event) => {
            if (event.target.type === "checkbox" && event.target.dataset.filterGroup) {
                const filterGroup = event.target.dataset.filterGroup;
                const filterValue = event.target.value;
                if (event.target.checked) {
                    if (!activeFilters[filterGroup].includes(filterValue)) {
                        activeFilters[filterGroup].push(filterValue);
                    }
                } else {
                    activeFilters[filterGroup] = activeFilters[filterGroup].filter(item => item !== filterValue);
                }
                applyAllFilters();
            }
        });
    }


    // Event listener for sort dropdown
    if (sortDropdown) {
        sortDropdown.addEventListener("change", () => {
            // Re-sort and render the currently filtered list
            if (currentlyDisplayedSyllabi.length > 0) {
                const sorted = sortSyllabi(currentlyDisplayedSyllabi, sortDropdown.value);
                renderSyllabusCards(sorted);
                 // Update currentlyDisplayedSyllabi to reflect the new sort order for subsequent operations if any
                 currentlyDisplayedSyllabi = sorted;
            }
        });
    }

    // Mobile Filter Panel Toggle
    if (mobileFilterToggleButton && filterPanel) {
        const filterContentContainer = filterPanel.querySelector("div:not(#mobile-filter-toggle)"); // Selects the main content div inside panel

        // Set initial state for button text and aria-expanded
        if (filterContentContainer) {
            const isInitiallyHidden = filterContentContainer.classList.contains("hidden");
            mobileFilterToggleButton.setAttribute("aria-expanded", String(!isInitiallyHidden));
            mobileFilterToggleButton.textContent = isInitiallyHidden ? "Show Filters" : "Hide Filters";
        }

        mobileFilterToggleButton.addEventListener("click", () => {
            if (filterContentContainer) {
                filterContentContainer.classList.toggle("hidden");
                const isExpanded = !filterContentContainer.classList.contains("hidden");
                mobileFilterToggleButton.setAttribute("aria-expanded", String(isExpanded));
                mobileFilterToggleButton.textContent = isExpanded ? "Hide Filters" : "Show Filters";
            }
        });
    }


    // Function to fetch syllabus data
    async function fetchSyllabi() {
        try {
            const response = await fetch(syllabiDataPath);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            allSyllabi = await response.json();
            populateDynamicFilters(allSyllabi); // Populate filters after data is fetched
            // Initialize activeFilters with available options from data (optional, but good for dynamic filters)
            // For now, filters are static in HTML.

            currentlyDisplayedSyllabi = [...allSyllabi];
            // applyAllFilters will now handle the initial sort based on sortDropdown.value
            applyAllFilters(); // Apply any default or persisted filters on load
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
