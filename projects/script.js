document.addEventListener('DOMContentLoaded', () => {
    // State Management
    let projectsData = [];
    let activeFilter = 'all';
    let searchQuery = '';

    // Tag Display overrides for polished capitalization
    const tagDisplayOverrides = {
        'palo alto': 'Palo Alto',
        'servicenow': 'ServiceNow',
        'cybersecurity': 'Cybersecurity'
    };

    // Elements
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    const projectsGrid = document.getElementById('projects-grid');
    const searchInput = document.getElementById('search-input');
    const tagFiltersList = document.getElementById('tag-filters-list');
    const postOverlay = document.getElementById('post-overlay');
    const closeOverlayBtn = document.getElementById('close-overlay');
    const articleContent = document.getElementById('article-content');

    // 1. Tab Switching Logic
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Update active state in buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            });
            button.classList.add('active');
            button.setAttribute('aria-selected', 'true');

            // Update visible panels
            tabPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.getAttribute('id') === `tab-${targetTab}`) {
                    panel.classList.add('active');
                }
            });
        });
    });

    // 2. Fetch Projects Data
    async function fetchProjects() {
        try {
            const response = await fetch(`./posts.json?_t=${Date.now()}`);
            if (!response.ok) {
                throw new Error('Failed to load portfolio database.');
            }
            projectsData = await response.json();
            
            // Initialize Grid & Filter tags
            renderTagFilters();
            renderProjects();
        } catch (error) {
            console.error(error);
            renderErrorState();
        }
    }

    // 3. Render Tag Filters
    function renderTagFilters() {
        // Collect all unique tags
        const allTags = new Set();
        projectsData.forEach(project => {
            if (project.tags && Array.isArray(project.tags)) {
                project.tags.forEach(tag => allTags.add(tag.toLowerCase()));
            }
        });

        // Clear existing dynamic tags (keep the "All" tag)
        tagFiltersList.innerHTML = '<button class="filter-tag active" data-tag="all">All</button>';

        // Append unique tags
        allTags.forEach(tag => {
            const btn = document.createElement('button');
            btn.className = 'filter-tag';
            btn.setAttribute('data-tag', tag);
            // Capitalize or override tag display
            const displayName = tagDisplayOverrides[tag.toLowerCase()] || (tag.charAt(0).toUpperCase() + tag.slice(1));
            btn.textContent = displayName;
            tagFiltersList.appendChild(btn);
        });

        // Add event listeners to newly created tags
        const filterTags = tagFiltersList.querySelectorAll('.filter-tag');
        filterTags.forEach(tagBtn => {
            tagBtn.addEventListener('click', () => {
                filterTags.forEach(t => t.classList.remove('active'));
                tagBtn.classList.add('active');
                activeFilter = tagBtn.getAttribute('data-tag');
                renderProjects();
            });
        });
    }

    // 4. Render Projects Cards
    function renderProjects() {
        // Clear grid
        projectsGrid.innerHTML = '';

        // Filter projects based on search query and category tags
        const filteredProjects = projectsData.filter(project => {
            const matchesSearch = 
                project.title.toLowerCase().includes(searchQuery) ||
                project.description.toLowerCase().includes(searchQuery) ||
                (project.tags && project.tags.some(t => t.toLowerCase().includes(searchQuery)));
            
            const matchesTag = activeFilter === 'all' || 
                (project.tags && project.tags.some(t => t.toLowerCase() === activeFilter));

            return matchesSearch && matchesTag;
        });

        // If no projects found, render empty state
        if (filteredProjects.length === 0) {
            renderEmptyState();
            return;
        }

        // Render cards
        filteredProjects.forEach(project => {
            const card = document.createElement('div');
            card.className = 'glow-card';
            card.setAttribute('data-slug', project.slug);
            
            // Tags HTML with proper casing overrides
            const tagsHtml = project.tags ? project.tags.map(t => {
                const tLower = t.toLowerCase();
                const displayName = tagDisplayOverrides[tLower] || t;
                return `<span class="card-tag">${displayName}</span>`;
            }).join('') : '';
            
            card.innerHTML = `
                <div class="card-banner">
                    <img src="${project.cover_image || './assets/placeholder.png'}" alt="${project.title}">
                    <div class="card-banner-overlay"></div>
                    <span class="card-category">${project.category || 'Engineering'}</span>
                </div>
                <div class="card-info">
                    <div class="card-meta">
                        <span>${project.date}</span>
                        <span class="card-meta-dot"></span>
                        <span>${project.read_time || '5 min read'}</span>
                    </div>
                    <h3 class="card-title">${project.title}</h3>
                    <p class="card-desc">${project.description}</p>
                    <div class="card-tags">
                        ${tagsHtml}
                    </div>
                </div>
            `;

            // Card click open overlay
            card.addEventListener('click', () => {
                openPostOverlay(project.slug);
            });

            projectsGrid.appendChild(card);
        });
    }

    // 5. Search Bar Event Listener
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            renderProjects();
        });
    }

    // 6. Detailed Overlay Reader Logic
    async function openPostOverlay(slug) {
        // Show loading state inside overlay
        articleContent.innerHTML = `
            <div class="loading-state" style="background:transparent; border:none; box-shadow:none;">
                <div class="spinner"></div>
                <p>Loading full report...</p>
            </div>
        `;
        
        // Show overlay with class
        postOverlay.classList.add('active');
        postOverlay.setAttribute('aria-hidden', 'false');
        // Lock body scrolling
        document.body.style.overflow = 'hidden';

        try {
            // Fetch individual post file
            const response = await fetch(`./posts/${slug}.json?_t=${Date.now()}`);
            if (!response.ok) {
                throw new Error('Could not retrieve detailed report content.');
            }
            const post = await response.json();

            // Populate overlay with premium article structure
            articleContent.innerHTML = `
                <header class="article-header">
                    <div class="article-header-meta">
                        <span>${post.category || 'Special Project'}</span>
                        <span>•</span>
                        <span>${post.read_time || '5 min read'}</span>
                    </div>
                    <h1 class="article-header-title">${post.title}</h1>
                    <div class="article-header-date">Published on ${post.date}</div>
                </header>

                ${post.cover_image ? `
                    <div class="article-cover">
                        <img src="${post.cover_image}" alt="${post.title}">
                    </div>
                ` : ''}

                <div class="article-body">
                    ${post.content}
                </div>
            `;
        } catch (error) {
            console.error(error);
            articleContent.innerHTML = `
                <div class="empty-state" style="background:transparent; border:none; box-shadow:none;">
                    <p style="color:#ef4444; font-weight:500;">Failed to load project details.</p>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    // 7. Close Overlay Logic
    function closePostOverlay() {
        postOverlay.classList.remove('active');
        postOverlay.setAttribute('aria-hidden', 'true');
        // Restore body scrolling
        document.body.style.overflow = '';
        articleContent.innerHTML = '';
    }

    if (closeOverlayBtn) {
        closeOverlayBtn.addEventListener('click', closePostOverlay);
    }

    // Close overlay on background click
    postOverlay.addEventListener('click', (e) => {
        if (e.target === postOverlay) {
            closePostOverlay();
        }
    });

    // Close overlay on ESC key press
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && postOverlay.classList.contains('active')) {
            closePostOverlay();
        }
    });

    // 8. Helper States Rendering
    function renderEmptyState() {
        projectsGrid.innerHTML = `
            <div class="empty-state">
                <p>No matching projects or posts found.</p>
            </div>
        `;
    }

    function renderErrorState() {
        projectsGrid.innerHTML = `
            <div class="empty-state">
                <p style="color:#ef4444; font-weight:500;">Error loading engineering database.</p>
                <p>Please check your connection or build logs.</p>
            </div>
        `;
    }

    // Kick-off database fetch
    fetchProjects();
});
