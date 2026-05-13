    <script>
        let currentPapers = [];

        document.getElementById('search_btn').addEventListener('click', async () => {
            const firstName = document.getElementById('first_name').value.trim();
            const lastName = document.getElementById('last_name').value.trim();

            if (!firstName || !lastName) {
                alert('Please enter both First Name and Last Name.');
                return;
            }

            const searchBtn = document.getElementById('search_btn');
            searchBtn.textContent = 'Searching...';
            searchBtn.disabled = true;

            document.getElementById('researchers_list').innerHTML = '<p class="text-on-surface-variant">Loading researchers...</p>';
            document.getElementById('papers_list').innerHTML = '';
            document.getElementById('papers_count').textContent = '0 Papers Found';
            document.getElementById('result_container').classList.add('hidden');
            currentPapers = [];

            try {
                const res = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ first_name: firstName, last_name: lastName })
                });
                const data = await res.json();

                if (data.researchers && data.researchers.length > 0) {
                    renderResearchers(data.researchers);
                } else {
                    document.getElementById('researchers_list').innerHTML = '<p class="text-error">No researchers found.</p>';
                }
            } catch (err) {
                console.error(err);
                document.getElementById('researchers_list').innerHTML = '<p class="text-error">Error fetching researchers.</p>';
            } finally {
                searchBtn.textContent = 'Search Academic Records';
                searchBtn.disabled = false;
            }
        });

        function renderResearchers(researchers) {
            const list = document.getElementById('researchers_list');
            list.innerHTML = '';

            researchers.forEach(r => {
                const card = document.createElement('div');
                card.className = "group bg-surface-container-lowest p-gutter border border-slate-200 rounded-lg flex justify-between items-center hover:shadow-md transition-all cursor-pointer";
                card.innerHTML = `
                <div class="flex items-center gap-gutter">
                    <div class="w-12 h-12 rounded-full overflow-hidden bg-slate-200 flex items-center justify-center font-bold text-slate-500">
                        ${r.display_name.charAt(0)}
                    </div>
                    <div>
                        <p class="font-h3 text-h3 text-primary">${r.display_name}</p>
                        <p class="text-body-sm text-slate-500">${r.count} Papers</p>
                    </div>
                </div>
                <button class="text-primary hover:underline font-label-caps select-profile-btn" data-id="${r.researcher_id}">Select Profile</button>
            `;
                list.appendChild(card);
            });

            document.querySelectorAll('.select-profile-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const rid = e.target.getAttribute('data-id');
                    // Optional: add visual active state
                    document.querySelectorAll('.select-profile-btn').forEach(b => b.textContent = 'Select Profile');
                    e.target.textContent = 'Selected';
                    fetchPapers(rid);
                });
            });
        }

        async function fetchPapers(researcherId) {
            const list = document.getElementById('papers_list');
            list.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-on-surface-variant">Loading papers...</td></tr>';

            try {
                const res = await fetch('/api/papers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ researcher_id: researcherId })
                });
                const data = await res.json();

                if (data.papers) {
                    currentPapers = data.papers;
                    renderPapers();
                }
            } catch (err) {
                console.error(err);
                list.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-error">Error fetching papers.</td></tr>';
            }
        }

        function renderPapers() {
            const list = document.getElementById('papers_list');
            list.innerHTML = '';
            document.getElementById('papers_count').textContent = \`\${currentPapers.length} Papers Found\`;
        
        currentPapers.forEach((p, idx) => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50 transition-colors";
            tr.innerHTML = \`
                <td class="px-gutter py-4">
                    <p class="font-body-md font-semibold text-primary">\${p.title}</p>
                    <p class="text-body-sm text-on-surface-variant italic">\${p.journal}, \${p.year}</p>
                </td>
                <td class="px-gutter py-4 text-right font-mono text-primary">\${p.times_cited}</td>
                <td class="px-gutter py-4 text-center">
                    <button class="text-slate-400 hover:text-error transition-colors remove-paper-btn" data-idx="\${idx}">
                        <span class="material-symbols-outlined" data-icon="close">close</span>
                    </button>
                </td>
            \`;
            list.appendChild(tr);
        });

        document.querySelectorAll('.remove-paper-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
                currentPapers.splice(idx, 1);
                renderPapers();
            });
        });
    }

    document.getElementById('calculate_btn').addEventListener('click', async () => {
        if (currentPapers.length === 0) {
            alert('No papers selected for calculation.');
            return;
        }

        const calcBtn = document.getElementById('calculate_btn');
        const originalText = calcBtn.innerHTML;
        calcBtn.innerHTML = '<span class="material-symbols-outlined" style="font-variation-settings: \\'FILL\\' 1;">hourglass_empty</span> Calculating...';
        calcBtn.disabled = true;

        try {
            const res = await fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ papers: currentPapers })
            });
            const data = await res.json();
            
            if (data.pindex !== undefined && data.pindex !== null) {
                document.getElementById('result_container').classList.remove('hidden');
                // Format to 2 decimal places
                document.getElementById('result_value').textContent = parseFloat(data.pindex).toFixed(2);
            } else {
                alert('Could not calculate p-index. Result was null.');
            }
        } catch (err) {
            console.error(err);
            alert('Error calculating p-index.');
        } finally {
            calcBtn.innerHTML = originalText;
            calcBtn.disabled = false;
        }
    });
    </script>
