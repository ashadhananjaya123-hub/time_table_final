/**
 * TimetablePro - Administrator Dashboard Controller
 * Manages Bento grid dashboards, dynamic directories, timetable generation,
 * interactive cell-by-cell slot editing, faculty analytics with Chart.js,
 * FullCalendar feeds, lost-class recovery, and activity periods.
 */

let activeTimetable = null;
let currentTimetableSlots = [];
let allDepartments = [];
let allTeachers = [];
let allClassrooms = [];
let allSubjects = [];

let overviewChartInstance = null;
let facultyBarChartInstance = null;
let deptDoughnutChartInstance = null;
let adminCalendarInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initAdminData();
    initAdminCalendar();
    loadDashboardStats();
    filterSubjectsTable();
    filterFacilitiesTable();
    filterDepartmentsTable();
});

async function initAdminData() {
    // Fetch common master records
    const [deptsRes, tchRes, roomsRes, subsRes] = await Promise.all([
        apiCall('/api/departments'),
        apiCall('/api/teachers'),
        apiCall('/api/classrooms'),
        apiCall('/api/subjects')
    ]);

    if (deptsRes.success) allDepartments = deptsRes.departments;
    if (tchRes.success) allTeachers = tchRes.teachers;
    if (roomsRes.success) allClassrooms = roomsRes.classrooms;
    if (subsRes.success) allSubjects = subsRes.subjects;

    populateAllDropdowns();
}

function populateAllDropdowns() {
    const deptOptions = allDepartments.map(d => `<option value="${d.id}">${d.code} - ${d.name}</option>`).join('');
    
    // Quick generate select
    const qDept = document.getElementById('quickDeptSelect');
    if (qDept) qDept.innerHTML = deptOptions;

    // Timetable filter dept
    const ttDept = document.getElementById('ttFilterDept');
    if (ttDept) ttDept.innerHTML = deptOptions;

    // Analytics dept filter
    const anDept = document.getElementById('analyticsDeptFilter');
    if (anDept) anDept.innerHTML = '<option value="all">All Academic Departments</option>' + deptOptions;

    // Analytics teacher filter
    const anTch = document.getElementById('analyticsTeacherFilter');
    if (anTch) {
        anTch.innerHTML = '<option value="all">All Faculty Members</option>' +
            allTeachers.map(t => `<option value="${t.id}">${t.name} (${t.department_code || 'Faculty'})</option>`).join('');
    }

    // Modal teacher dept
    const mTDept = document.getElementById('modalTDept');
    if (mTDept) mTDept.innerHTML = deptOptions;

    // Modal student dept
    const mSDept = document.getElementById('modalSDept');
    if (mSDept) mSDept.innerHTML = deptOptions;

    // Filter teacher dept
    const fTDept = document.getElementById('filterTeacherDept');
    if (fTDept) fTDept.innerHTML = '<option value="all">All Departments</option>' + deptOptions;

    // Master calendar dept filter
    const calDept = document.getElementById('calFilterDept');
    if (calDept) calDept.innerHTML = '<option value="all">All Departments</option>' + deptOptions;

    // Filter student dept
    const fSDept = document.getElementById('filterStudentDept');
    if (fSDept) fSDept.innerHTML = '<option value="all">All Departments</option>' + deptOptions;

    // Filter curriculum subject dept
    const fSubDept = document.getElementById('filterSubjectDept');
    if (fSubDept) fSubDept.innerHTML = '<option value="all">All Departments</option>' + deptOptions;

    // Modal add subject dept
    const mSubDept = document.getElementById('modalSubDept');
    if (mSubDept) mSubDept.innerHTML = deptOptions;

    // Modal add subject teacher
    const mSubTch = document.getElementById('modalSubTeacher');
    if (mSubTch) {
        mSubTch.innerHTML = '<option value="">-- Optional: Assign Instructor --</option>' +
            allTeachers.map(t => `<option value="${t.id}">${t.name} (${t.department_code || 'Faculty'})</option>`).join('');
    }

    // Event affected dept
    const evDept = document.getElementById('evDept');
    if (evDept) evDept.innerHTML = '<option value="">All Departments</option>' + deptOptions;

    // Announcement target dept
    const annDept = document.getElementById('annTargetDeptInput');
    if (annDept) annDept.innerHTML = '<option value="all">Campus Wide (All Students & Faculty)</option>' + deptOptions;

    // Extra class subjects
    const extSub = document.getElementById('extraSubjectSelect');
    if (extSub) {
        extSub.innerHTML = '<option value="">Select Subject</option>' +
            allSubjects.map(s => `<option value="${s.id}" data-teacher="${s.teacher_id}">${s.code} - ${s.name} (${s.department_code})</option>`).join('');
    }

    // Extra class teachers
    const extTch = document.getElementById('extraTeacherSelect');
    if (extTch) {
        extTch.innerHTML = '<option value="">Select Faculty</option>' +
            allTeachers.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
    }

    // Extra class rooms
    const extRoom = document.getElementById('extraRoomSelect');
    if (extRoom) {
        extRoom.innerHTML = allClassrooms.map(r => `<option value="${r.id}">${r.name} (${r.type})</option>`).join('');
    }

    // Edit slot rooms
    const editRoom = document.getElementById('editSlotRoom');
    if (editRoom) {
        editRoom.innerHTML = '<option value="">-- Select Room --</option>' +
            allClassrooms.map(r => `<option value="${r.id}">${r.name} (${r.type})</option>`).join('');
    }

    // Edit slot teachers
    const editTch = document.getElementById('editSlotTeacher');
    if (editTch) {
        editTch.innerHTML = '<option value="">-- Auto-select from subject default --</option>' +
            allTeachers.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
    }
}

/* ==========================================================================
   1. Dashboard Overview Metrics & Charts
   ========================================================================== */

async function loadDashboardStats() {
    const res = await apiCall('/api/admin/stats');
    if (res.success) {
        document.getElementById('statFacultyCount').textContent = res.counts.teachers;
        document.getElementById('statStudentCount').textContent = res.counts.students;
        document.getElementById('statTimetablesCount').textContent = res.counts.timetables;
        document.getElementById('statPendingSwaps').textContent = res.counts.pending_swaps;

        // Render recent swaps feed
        const swapsContainer = document.getElementById('dashboardRecentSwapsList');
        if (swapsContainer) {
            if (res.recent_swaps && res.recent_swaps.length > 0) {
                swapsContainer.innerHTML = res.recent_swaps.map(sw => `
                    <div class="p-2 rounded border bg-light" style="font-size: 0.8rem;">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong>${sw.sender_name} ⇄ ${sw.receiver_name}</strong>
                            <span class="badge-pill success">Executed</span>
                        </div>
                        <div class="text-secondary" style="font-size: 0.75rem;">${sw.details}</div>
                        <div class="text-muted" style="font-size: 0.68rem; margin-top: 2px;">${formatDate(sw.executed_at)}</div>
                    </div>
                `).join('');
            } else {
                swapsContainer.innerHTML = '<div class="text-muted text-center py-3" style="font-size: 0.8rem;">No recent mutual teacher swaps logged.</div>';
            }
        }

        // Render recent announcements
        const annContainer = document.getElementById('dashboardRecentAnnouncementsList');
        if (annContainer) {
            if (res.recent_announcements && res.recent_announcements.length > 0) {
                annContainer.innerHTML = res.recent_announcements.map(ann => `
                    <div class="p-2 rounded border bg-light" style="font-size: 0.8rem;">
                        <div class="fw-bold text-dark">${ann.title}</div>
                        <div class="text-secondary" style="font-size: 0.75rem;">${ann.content.substring(0, 85)}...</div>
                        <div class="text-muted" style="font-size: 0.68rem; margin-top: 2px;">${formatDate(ann.created_at)}</div>
                    </div>
                `).join('');
            } else {
                annContainer.innerHTML = '<div class="text-muted text-center py-3" style="font-size: 0.8rem;">No campus notices active.</div>';
            }
        }
    }

    loadOverviewChart();
}

async function loadOverviewChart() {
    const res = await apiCall('/api/analytics/workload');
    if (!res.success) return;

    const ctx = document.getElementById('overviewWorkloadChart');
    if (!ctx) return;

    if (overviewChartInstance) overviewChartInstance.destroy();

    const chartData = res.analytics.charts.bar;
    overviewChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Assigned Periods',
                    data: chartData.assigned,
                    backgroundColor: '#4f46e5',
                    borderRadius: 4
                },
                {
                    label: 'Available Teaching Periods',
                    data: chartData.available,
                    backgroundColor: '#e2e8f0',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                y: { beginAtZero: true, max: 48, ticks: { stepSize: 8, font: { size: 10 } } },
                x: { ticks: { font: { size: 10 } } }
            }
        }
    });
}

/* ==========================================================================
   2. Timetable Generation & Interactive Slot Editor
   ========================================================================== */

async function handleQuickGenerate(e) {
    e.preventDefault();
    const dept = document.getElementById('quickDeptSelect').value;
    const year = document.getElementById('quickYearSelect').value;
    const sem = document.getElementById('quickSemSelect').value;
    const sec = document.getElementById('quickSecSelect')?.value || 'A';

    const btn = document.getElementById('btnQuickGen');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generating...';

    const res = await apiCall('/api/timetables/generate', 'POST', {
        department_id: dept,
        year: year,
        semester: sem,
        section: sec
    });

    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="play" style="width: 16px; height: 16px;"></i><span>Generate Non-Conflicting Schedule</span>';
    initLucideIcons();

    if (res.success) {
        showToast('Timetable generated with 0 conflicts!', 'success');
        // Switch to timetable section and view it
        document.getElementById('ttFilterDept').value = dept;
        document.getElementById('ttFilterYear').value = year;
        onTtYearChange();
        document.getElementById('ttFilterSem').value = sem;
        if (document.getElementById('ttFilterSec')) document.getElementById('ttFilterSec').value = sec;
        showBentoSection('timetables');
        loadSelectedTimetable();
    } else {
        const errorMsg = res.errors ? res.errors.join('<br>') : res.message;
        showToast('Generation halted: ' + (res.errors ? res.errors[0] : res.message), 'danger');
    }
}

function onQuickYearChange() {
    const yVal = parseInt(document.getElementById('quickYearSelect')?.value || '1');
    const s1 = (yVal - 1) * 2 + 1;
    const s2 = s1 + 1;
    const semEl = document.getElementById('quickSemSelect');
    if (semEl) {
        semEl.innerHTML = `
            <option value="${s1}" selected>Semester ${s1}</option>
            <option value="${s2}">Semester ${s2}</option>
        `;
    }
}

function onTtYearChange() {
    const yVal = parseInt(document.getElementById('ttFilterYear')?.value || '1');
    const s1 = (yVal - 1) * 2 + 1;
    const s2 = s1 + 1;
    const semEl = document.getElementById('ttFilterSem');
    if (semEl) {
        semEl.innerHTML = `
            <option value="${s1}" selected>Semester ${s1}</option>
            <option value="${s2}">Semester ${s2}</option>
        `;
    }
    loadSelectedTimetable();
}

async function loadSelectedTimetable() {
    const dept = document.getElementById('ttFilterDept')?.value;
    const year = document.getElementById('ttFilterYear')?.value;
    const sem = document.getElementById('ttFilterSem')?.value;
    const sec = document.getElementById('ttFilterSec')?.value || 'A';

    const display = document.getElementById('adminTimetableDisplay');
    const banner = document.getElementById('timetableStatusBanner');
    const btnPub = document.getElementById('btnPublishTT');
    const btnUnpub = document.getElementById('btnUnpublishTT');
    const btnDel = document.getElementById('btnDeleteTT');

    if (!dept || !year || !sem) return;

    display.innerHTML = '<div style="padding: 2.5rem; text-align: center; color: var(--slate-400);">Loading schedule...</div>';

    const res = await apiCall(`/api/timetables?department_id=${dept}&year=${year}&semester=${sem}&section=${encodeURIComponent(sec)}`);
    if (!res.success) return;

    activeTimetable = res.timetable;
    currentTimetableSlots = res.slots || [];

    if (!activeTimetable) {
        banner.innerHTML = `
            <div class="alert alert-warning py-2 d-flex align-items-center justify-content-between" style="font-size: 0.85rem;">
                <div class="d-flex align-items-center gap-2">
                    <i data-lucide="alert-circle" style="width: 16px; height: 16px;"></i>
                    <span>No timetable currently generated for this department and semester.</span>
                </div>
                <button class="btn btn-sm btn-indigo" onclick="generateCurrentTimetable()">Generate Now</button>
            </div>
        `;
        display.innerHTML = `
            <div style="padding: 3.5rem; text-align: center; color: var(--slate-400);">
                <i data-lucide="calendar-plus" style="width: 36px; height: 36px; stroke-width: 1.5; margin-bottom: 0.5rem;"></i>
                <div>Click "Generate Schedule" above to automatically produce a conflict-free master timetable.</div>
            </div>
        `;
        btnPub.style.display = 'none';
        btnUnpub.style.display = 'none';
        btnDel.style.display = 'none';
        initLucideIcons();
        return;
    }

    // Toggle publish/unpublish buttons
    btnDel.style.display = 'inline-flex';
    if (activeTimetable.published) {
        btnPub.style.display = 'none';
        btnUnpub.style.display = 'inline-flex';
        banner.innerHTML = `
            <div class="alert alert-success py-2 d-flex align-items-center justify-content-between" style="font-size: 0.85rem;">
                <div class="d-flex align-items-center gap-2">
                    <i data-lucide="check-circle" style="width: 16px; height: 16px;"></i>
                    <span>Official Timetable is <strong>Published & Active</strong> (visible to students and faculty).</span>
                </div>
                <span class="badge-pill success">Live</span>
            </div>
        `;
    } else {
        btnPub.style.display = 'inline-flex';
        btnUnpub.style.display = 'none';
        banner.innerHTML = `
            <div class="alert alert-secondary py-2 d-flex align-items-center justify-content-between" style="font-size: 0.85rem;">
                <div class="d-flex align-items-center gap-2">
                    <i data-lucide="eye-off" style="width: 16px; height: 16px;"></i>
                    <span>Timetable is currently in <strong>Draft Status</strong> (hidden from students).</span>
                </div>
                <button class="btn btn-sm btn-success" onclick="publishActiveTimetable()">Publish to Campus</button>
            </div>
        `;
    }

    renderTimetableGrid(display, res.slots, res.periods_config, res.days_config);
    initLucideIcons();
}

function renderTimetableGrid(container, slots, periods, days) {
    // Map slots by key (day, period)
    const slotMap = {};
    slots.forEach(s => {
        slotMap[`${s.day}_${s.period}`] = s;
    });

    let html = `
        <table class="timetable-table">
            <thead>
                <tr>
                    <th class="time-col">Period / Time</th>
                    ${days.map(d => `<th>${d}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    periods.forEach(p => {
        // Morning Break after period 3
        if (p.number === 4) {
            html += `
                <tr class="break-interval-row">
                    <td>11:30 - 11:45</td>
                    <td colspan="6">Morning Refreshment Break (15 mins)</td>
                </tr>
            `;
        }
        // Lunch Break after period 5
        if (p.number === 6) {
            html += `
                <tr class="break-interval-row">
                    <td>01:25 - 02:00</td>
                    <td colspan="6">Institutional Lunch Break Interval (35 mins)</td>
                </tr>
            `;
        }

        html += `
            <tr>
                <td class="time-col">
                    <div style="font-weight: 700;">Period ${p.number}</div>
                    <div style="font-size: 0.7rem; color: var(--slate-400);">${p.start} - ${p.end}</div>
                </td>
        `;

        days.forEach(d => {
            const slot = slotMap[`${d}_${p.number}`];
            if (slot) {
                const isLab = slot.slot_type === 'lab';
                const isAct = slot.slot_type === 'activity';
                const isExt = slot.slot_type === 'extra';

                let cellClass = 'period-cell';
                if (isLab) cellClass += ' cell-lab';
                else if (isAct) cellClass += ' cell-activity';
                else if (isExt) cellClass += ' cell-extra';

                html += `
                    <td>
                        <div class="${cellClass}" onclick="openSlotEditor('${slot.id}', '${d}', ${p.number})" title="Click to edit slot">
                            <span class="slot-code">${slot.subject_code || (isAct ? 'ACTIVITY' : 'CLASS')}</span>
                            <span class="slot-name">${slot.subject_name || (isAct ? 'Sports/Club Session' : '')}</span>
                            <span class="slot-meta">${slot.teacher_name ? slot.teacher_name.split(' ').slice(0, 2).join(' ') : 'TBD'}</span>
                            <span class="slot-meta">${slot.classroom_name || 'Room'}</span>
                        </div>
                    </td>
                `;
            } else {
                html += `
                    <td>
                        <div class="empty-slot" onclick="openNewSlotEditor('${d}', ${p.number})">
                            + Free
                        </div>
                    </td>
                `;
            }
        });

        html += `</tr>`;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

async function generateCurrentTimetable() {
    const dept = document.getElementById('ttFilterDept')?.value;
    const year = document.getElementById('ttFilterYear')?.value;
    const sem = document.getElementById('ttFilterSem')?.value;
    const sec = document.getElementById('ttFilterSec')?.value || 'A';

    const res = await apiCall('/api/timetables/generate', 'POST', {
        department_id: dept,
        year: year,
        semester: sem,
        section: sec
    });

    if (res.success) {
        showToast('Timetable generated successfully!', 'success');
        loadSelectedTimetable();
        loadDashboardStats();
    } else {
        showToast(res.errors ? res.errors[0] : res.message, 'danger');
    }
}

async function publishActiveTimetable() {
    if (!activeTimetable) return;
    const res = await apiCall(`/api/timetables/${activeTimetable.id}/publish`, 'POST');
    if (res.success) {
        showToast('Timetable published to campus!', 'success');
        loadSelectedTimetable();
        loadDashboardStats();
    }
}

async function unpublishActiveTimetable() {
    if (!activeTimetable) return;
    const res = await apiCall(`/api/timetables/${activeTimetable.id}/unpublish`, 'POST');
    if (res.success) {
        showToast('Timetable reverted to draft.', 'warning');
        loadSelectedTimetable();
        loadDashboardStats();
    }
}

async function deleteActiveTimetable() {
    if (!activeTimetable) return;
    if (!confirm('Are you sure you want to delete this timetable and all its assigned slots?')) return;

    const res = await apiCall(`/api/timetables/${activeTimetable.id}`, 'DELETE');
    if (res.success) {
        showToast('Timetable deleted.', 'info');
        loadSelectedTimetable();
        loadDashboardStats();
    }
}

function openSlotEditor(slotId, day, period) {
    const slot = currentTimetableSlots.find(s => s.id == slotId);
    if (!slot) return;

    document.getElementById('editSlotId').value = slotId;
    document.getElementById('editSlotMetaDesc').textContent = `${day}, Period ${period} (${slot.subject_code || 'Unassigned'})`;

    // Populate subjects for current timetable's dept/year/sem
    const deptSubjects = allSubjects.filter(s => s.department_id === activeTimetable.department_id && s.year == activeTimetable.year && s.semester == activeTimetable.semester);
    const subSelect = document.getElementById('editSlotSubject');
    subSelect.innerHTML = '<option value="">-- Free Period --</option>' +
        deptSubjects.map(s => `<option value="${s.id}" data-teacher="${s.teacher_id}" ${s.id === slot.subject_id ? 'selected' : ''}>${s.code} - ${s.name} (${s.type})</option>`).join('');

    document.getElementById('editSlotTeacher').value = slot.teacher_id || '';
    document.getElementById('editSlotRoom').value = slot.classroom_id || '';
    document.getElementById('editSlotType').value = slot.slot_type || 'regular';

    openModal('modalEditSlot');
}

function autoAssignSlotTeacher() {
    const subSelect = document.getElementById('editSlotSubject');
    const opt = subSelect.options[subSelect.selectedIndex];
    const defaultTch = opt.getAttribute('data-teacher');
    if (defaultTch && defaultTch !== 'null') {
        document.getElementById('editSlotTeacher').value = defaultTch;
    }
}

async function saveSlotEditSubmit(e) {
    e.preventDefault();
    const slotId = document.getElementById('editSlotId').value;
    const subId = document.getElementById('editSlotSubject').value;
    const tId = document.getElementById('editSlotTeacher').value;
    const rId = document.getElementById('editSlotRoom').value;
    const slotType = document.getElementById('editSlotType').value;

    const res = await apiCall(`/api/timetables/slots/${slotId}`, 'PUT', {
        subject_id: subId,
        teacher_id: tId,
        classroom_id: rId,
        slot_type: slotType
    });

    if (res.success) {
        showToast('Period slot updated successfully.', 'success');
        closeModal('modalEditSlot');
        loadSelectedTimetable();
    } else {
        showToast(res.message, 'danger');
    }
}

async function clearCurrentSlot() {
    const slotId = document.getElementById('editSlotId').value;
    const res = await apiCall(`/api/timetables/slots/${slotId}`, 'DELETE');
    if (res.success) {
        showToast('Period cleared to free.', 'info');
        closeModal('modalEditSlot');
        loadSelectedTimetable();
    }
}

/* ==========================================================================
   3. Faculty Workload & Utilization Analytics
   ========================================================================== */

async function loadAnalyticsData() {
    const dept = document.getElementById('analyticsDeptFilter')?.value;
    const tch = document.getElementById('analyticsTeacherFilter')?.value;

    const res = await apiCall(`/api/analytics/workload?department_id=${dept}&teacher_id=${tch}`);
    if (!res.success) return;

    const data = res.analytics;
    document.getElementById('analyticsAvgUtilBadge').textContent = `Average Utilization: ${data.summary.average_utilization_pct}%`;

    // Render Matrix Table
    const tbody = document.getElementById('utilizationMatrixTableBody');
    if (tbody) {
        tbody.innerHTML = data.faculty_metrics.map(f => {
            let statusBadge = '<span class="badge-pill success">Optimal</span>';
            if (f.status === 'high') statusBadge = '<span class="badge-pill danger">High Load</span>';
            else if (f.status === 'low') statusBadge = '<span class="badge-pill neutral">Light Load</span>';

            return `
                <tr>
                    <td><strong>${f.name}</strong></td>
                    <td><span class="badge-pill neutral">${f.department_code}</span></td>
                    <td><strong>${f.assigned_periods} hrs</strong> / week</td>
                    <td>${f.available_periods} hrs max</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="progress flex-grow-1" style="height: 6px;">
                                <div class="progress-bar ${f.utilization_pct > 65 ? 'bg-danger' : 'bg-primary'}" style="width: ${f.utilization_pct}%;"></div>
                            </div>
                            <span style="font-weight: 700; font-size: 0.78rem;">${f.utilization_pct}%</span>
                        </div>
                    </td>
                    <td>${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }

    // Render Bar Chart
    const ctxBar = document.getElementById('facultyBarChart');
    if (ctxBar) {
        if (facultyBarChartInstance) facultyBarChartInstance.destroy();
        facultyBarChartInstance = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: data.charts.bar.labels,
                datasets: [
                    {
                        label: 'Assigned Teaching Periods',
                        data: data.charts.bar.assigned,
                        backgroundColor: '#4f46e5',
                        borderRadius: 4
                    },
                    {
                        label: 'Available Institutional Periods',
                        data: data.charts.bar.available,
                        backgroundColor: '#e2e8f0',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true, max: 48 } }
            }
        });
    }

    // Render Doughnut Chart
    const ctxDoughnut = document.getElementById('deptDoughnutChart');
    if (ctxDoughnut) {
        if (deptDoughnutChartInstance) deptDoughnutChartInstance.destroy();
        deptDoughnutChartInstance = new Chart(ctxDoughnut, {
            type: 'doughnut',
            data: {
                labels: data.charts.doughnut.labels,
                datasets: [{
                    data: data.charts.doughnut.values,
                    backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

/* ==========================================================================
   4. Master Calendar (FullCalendar) - Clean Decluttered Multi-Perspective
   ========================================================================== */

function getCalendarEventsUrl() {
    const type = document.getElementById('calFilterType')?.value || 'institutional';
    const dept = document.getElementById('calFilterDept')?.value || 'all';
    const cohort = document.getElementById('calFilterCohort')?.value || 'all';

    let url = `/api/calendar/events?type=${encodeURIComponent(type)}`;
    if (dept !== 'all') {
        url += `&department_id=${encodeURIComponent(dept)}`;
    }
    if (cohort !== 'all') {
        const parts = cohort.split('_');
        if (parts.length === 2) {
            url += `&semester=${encodeURIComponent(parts[0])}&section=${encodeURIComponent(parts[1])}`;
        }
    }
    return url;
}

function initAdminCalendar() {
    const calendarEl = document.getElementById('adminFullCalendar');
    if (!calendarEl || !window.FullCalendar) return;

    adminCalendarInstance = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        slotMinTime: '08:30:00',
        slotMaxTime: '17:30:00',
        allDaySlot: true,
        nowIndicator: true,
        slotEventOverlap: true,
        dayMaxEvents: 4,
        views: {
            timeGrid: {
                dayMaxEventRows: 4
            }
        },
        events: getCalendarEventsUrl(),
        eventClick: function(info) {
            const props = info.event.extendedProps || {};
            let detail = `${info.event.title}`;
            if (props.subject) detail += `\nSubject: ${props.subject}`;
            if (props.cohort) detail += `\nCohort: ${props.cohort}`;
            if (props.room) detail += `\nClassroom: ${props.room}`;
            if (props.faculty) detail += `\nInstructor: ${props.faculty}`;
            if (props.description) detail += `\nDescription: ${props.description}`;
            alert(detail);
        }
    });

    adminCalendarInstance.render();
}

function refreshAdminCalendar() {
    if (!adminCalendarInstance) return;
    adminCalendarInstance.removeAllEventSources();
    adminCalendarInstance.addEventSource(getCalendarEventsUrl());
}

function resetCalendarFilter() {
    const typeEl = document.getElementById('calFilterType');
    const deptEl = document.getElementById('calFilterDept');
    const cohortEl = document.getElementById('calFilterCohort');
    if (typeEl) typeEl.value = 'institutional';
    if (deptEl) deptEl.value = 'all';
    if (cohortEl) cohortEl.value = 'all';
    refreshAdminCalendar();
}

/* ==========================================================================
   5. CRUD: Faculty, Students, Curriculum, Facilities, Departments
   ========================================================================== */

async function filterTeachersTable() {
    const search = document.getElementById('searchTeacherInput')?.value || '';
    const dept = document.getElementById('filterTeacherDept')?.value || 'all';

    const res = await apiCall(`/api/teachers?department_id=${dept}&search=${encodeURIComponent(search)}`);
    if (!res.success) return;

    const tbody = document.getElementById('teachersTableBody');
    if (!tbody) return;

    tbody.innerHTML = res.teachers.map(t => {
        const classes = t.classes_taken || [];
        const classesBadges = classes.length > 0 
            ? classes.slice(0, 3).map(c => `
                <span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:600; font-size:0.72rem; padding: 3px 6px;" title="${c.subject_name || ''}">
                    ${c.subject_code} <small class="text-muted" style="font-size:0.65rem;">(${c.cohort})</small>
                </span>
            `).join(' ') + (classes.length > 3 ? `<span class="badge bg-light text-muted border" style="font-size:0.7rem;">+${classes.length - 3} more</span>` : '')
            : '<span class="text-muted" style="font-size:0.78rem;">No classes assigned</span>';

        return `
            <tr>
                <td><strong>${t.name}</strong></td>
                <td><code>${t.username}</code></td>
                <td>${t.email || 'N/A'}<br><small class="text-muted">${t.phone || ''}</small></td>
                <td><span class="badge-pill neutral">${t.department_code || 'GEN'}</span></td>
                <td>
                    <div class="d-flex flex-wrap gap-1 align-items-center">
                        ${classesBadges}
                    </div>
                </td>
                <td><strong>${t.assigned_periods} hrs</strong> / week</td>
                <td class="text-end">
                    <div class="dropdown d-inline-block">
                        <button class="btn btn-sm btn-outline-indigo dropdown-toggle d-inline-flex align-items-center gap-1" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <i data-lucide="calendar" style="width: 14px; height: 14px;"></i> Schedule
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end shadow-sm" style="font-size: 0.82rem; min-width: 240px;">
                            <li>
                                <a class="dropdown-item d-flex align-items-center gap-2 text-indigo fw-semibold" href="#" onclick="viewTeacherSpecificTimetable('${t.id}', '${encodeURIComponent(t.name)}', '${encodeURIComponent(t.department_code || '')}'); return false;">
                                    <i data-lucide="table" style="width: 14px; height: 14px;"></i> View Weekly Routine
                                </a>
                            </li>
                            <li><hr class="dropdown-divider my-1"></li>
                            <li><h6 class="dropdown-header text-uppercase" style="font-size: 0.7rem; font-weight: 700;">Classes Taken (${classes.length})</h6></li>
                            ${classes.length > 0 ? classes.map(c => `
                                <li class="px-3 py-1" style="font-size: 0.78rem;">
                                    <span class="fw-bold text-dark">${c.subject_code}</span>: ${c.subject_name || ''}<br>
                                    <span class="badge bg-light text-secondary border">${c.cohort}</span>
                                </li>
                            `).join('') : '<li class="px-3 py-1 text-muted" style="font-size: 0.78rem;">No active classes assigned</li>'}
                        </ul>
                    </div>
                    <button class="btn btn-sm btn-outline-danger ms-1" onclick="deleteTeacherRecord('${t.id}')" title="Delete Faculty">
                        <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    initLucideIcons();
}

async function viewTeacherSpecificTimetable(teacherId, encodedName, encodedDept) {
    const teacherName = decodeURIComponent(encodedName || '');
    const deptCode = decodeURIComponent(encodedDept || 'GEN');

    const titleEl = document.getElementById('adminTeacherScheduleTitle');
    const subtitleEl = document.getElementById('adminTeacherScheduleSubtitle');
    const tbody = document.getElementById('adminTeacherScheduleTableBody');
    const badgesContainer = document.getElementById('adminTeacherClassesBadges');
    const loadEl = document.getElementById('adminTeacherTotalLoad');

    if (titleEl) titleEl.textContent = `Faculty Timetable Routine: ${teacherName}`;
    if (subtitleEl) subtitleEl.textContent = `Department: ${deptCode} | Live Synchronized Timetable`;
    if (badgesContainer) badgesContainer.innerHTML = '<span class="text-muted">Loading assigned classes...</span>';
    if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">Retrieving live teaching schedule...</td></tr>';

    openModal('modalViewTeacherSchedule');

    const res = await apiCall(`/api/teachers/${teacherId}`);
    if (!res.success) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-danger">Failed to load schedule.</td></tr>';
        return;
    }

    const slots = res.slots || [];
    const subjects = res.subjects || [];

    // Map unique courses taken
    const uniqueCourses = new Map();
    slots.forEach(s => {
        if (s.subject_code) {
            const secStr = s.section ? ` Sec ${s.section}` : '';
            const key = `${s.subject_code}_${s.semester}_${s.section}`;
            uniqueCourses.set(key, {
                code: s.subject_code,
                name: s.subject_name,
                cohort: `${s.dept_code || deptCode} S${s.semester}${secStr}`
            });
        }
    });

    if (badgesContainer) {
        if (uniqueCourses.size > 0) {
            badgesContainer.innerHTML = Array.from(uniqueCourses.values()).map(c => `
                <span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:600; font-size:0.75rem; padding: 4px 8px;">
                    ${c.code} (${c.cohort})
                </span>
            `).join(' ');
        } else {
            badgesContainer.innerHTML = '<span class="text-muted" style="font-size:0.78rem;">No active teaching assignments found in published timetable.</span>';
        }
    }

    if (loadEl) {
        loadEl.textContent = `${slots.length} Hours / Week`;
    }

    // Build slot lookup
    const slotMap = {};
    slots.forEach(s => {
        slotMap[`${s.day}_${s.period}`] = s;
    });

    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    if (tbody) {
        tbody.innerHTML = days.map(d => {
            let row = `<tr><td style="font-weight:700; background:#f8fafc;">${d.substring(0, 3)}</td>`;
            for (let p = 1; p <= 8; p++) {
                const s = slotMap[`${d}_${p}`];
                if (s) {
                    const isLab = s.slot_type === 'lab';
                    const bg = isLab ? '#d1fae5' : '#e0e7ff';
                    const color = isLab ? '#065f46' : '#3730a3';
                    const secLabel = s.section ? `-${s.section}` : '';
                    row += `
                        <td style="background-color: ${bg}; color: ${color}; padding: 6px 3px;">
                            <div style="font-weight:700; font-size:0.76rem;">${s.subject_code || 'Class'}</div>
                            <div style="font-size:0.68rem; opacity:0.9;">${s.classroom_name || 'Room'}</div>
                            <div style="font-size:0.65rem; font-weight:600;">[S${s.semester || ''}${secLabel}]</div>
                        </td>
                    `;
                } else {
                    row += `<td style="color: var(--slate-300); font-size: 0.75rem;">-</td>`;
                }
            }
            row += `</tr>`;
            return row;
        }).join('');
    }

    initLucideIcons();
}

async function saveTeacherSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('modalTName').value;
    const username = document.getElementById('modalTUser').value;
    const password = document.getElementById('modalTPass').value;
    const email = document.getElementById('modalTEmail').value;
    const dept = document.getElementById('modalTDept').value;

    const res = await apiCall('/api/teachers', 'POST', {
        name, username, password, email, department_id: dept
    });

    if (res.success) {
        showToast('Faculty member registered.', 'success');
        closeModal('modalAddTeacher');
        await initAdminData();
        filterTeachersTable();
        loadDashboardStats();
    } else {
        showToast(res.message, 'danger');
    }
}

async function deleteTeacherRecord(id) {
    if (!confirm('Remove this faculty member from the academic directory?')) return;
    const res = await apiCall(`/api/teachers/${id}`, 'DELETE');
    if (res.success) {
        showToast('Faculty member removed.', 'info');
        filterTeachersTable();
        loadDashboardStats();
    }
}

async function filterStudentsTable() {
    const search = document.getElementById('searchStudentInput')?.value || '';
    const dept = document.getElementById('filterStudentDept')?.value || 'all';
    const year = document.getElementById('filterStudentYear')?.value || 'all';
    const sem = document.getElementById('filterStudentSem')?.value || 'all';

    const res = await apiCall(`/api/students?department_id=${dept}&year=${year}&semester=${sem}&search=${encodeURIComponent(search)}`);
    if (!res.success) return;

    const tbody = document.getElementById('studentsTableBody');
    if (!tbody) return;

    tbody.innerHTML = res.students.map(s => `
        <tr>
            <td><code>${s.roll_no || 'N/A'}</code></td>
            <td><strong>${s.name}</strong></td>
            <td>${s.username}</td>
            <td><span class="badge-pill neutral">${s.department_code || 'None'}</span></td>
            <td>Year ${s.year}, Sem ${s.semester}</td>
            <td>Section ${s.section || 'A'}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-danger" onclick="deleteStudentRecord('${s.id}')">
                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                </button>
            </td>
        </tr>
    `).join('');

    initLucideIcons();
}

async function saveStudentSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('modalSName').value.trim();
    const roll = document.getElementById('modalSRoll').value.trim();
    const username = document.getElementById('modalSUser').value.trim();
    const password = document.getElementById('modalSPass').value;
    const dept = document.getElementById('modalSDept').value;
    const year = document.getElementById('modalSYear').value;
    const sem = document.getElementById('modalSSem').value;
    const section = document.getElementById('modalSSec')?.value || 'A';

    const res = await apiCall('/api/students', 'POST', {
        name, roll_no: roll, username, password, department_id: dept, year, semester: sem, section
    });

    if (res.success) {
        showToast('Student registered successfully.', 'success');
        closeModal('modalAddStudent');
        document.getElementById('modalSName').value = '';
        document.getElementById('modalSRoll').value = '';
        document.getElementById('modalSUser').value = '';
        filterStudentsTable();
        loadDashboardStats();
    } else {
        showToast(res.message, 'danger');
    }
}

function onStudentYearFilterChange() {
    const yVal = document.getElementById('filterStudentYear')?.value || 'all';
    const semEl = document.getElementById('filterStudentSem');
    if (semEl) {
        if (yVal === 'all') {
            semEl.innerHTML = `
                <option value="all">All Semesters</option>
                <option value="1">Sem 1</option><option value="2">Sem 2</option>
                <option value="3">Sem 3</option><option value="4">Sem 4</option>
                <option value="5">Sem 5</option><option value="6">Sem 6</option>
                <option value="7">Sem 7</option><option value="8">Sem 8</option>
            `;
        } else {
            const y = parseInt(yVal);
            const s1 = (y - 1) * 2 + 1;
            const s2 = s1 + 1;
            semEl.innerHTML = `
                <option value="all">All Year ${y} (Sem ${s1} & ${s2})</option>
                <option value="${s1}">Sem ${s1}</option>
                <option value="${s2}">Sem ${s2}</option>
            `;
        }
    }
    filterStudentsTable();
}

function onStudentModalYearChange() {
    const yVal = parseInt(document.getElementById('modalSYear')?.value || '1');
    const s1 = (yVal - 1) * 2 + 1;
    const s2 = s1 + 1;
    const semEl = document.getElementById('modalSSem');
    if (semEl) {
        semEl.innerHTML = `
            <option value="${s1}" selected>Sem ${s1}</option>
            <option value="${s2}">Sem ${s2}</option>
        `;
    }
}

async function deleteStudentRecord(id) {
    if (!confirm('Delete student record?')) return;
    const res = await apiCall(`/api/students/${id}`, 'DELETE');
    if (res.success) {
        showToast('Student deleted.', 'info');
        filterStudentsTable();
        loadDashboardStats();
    }
}

/* ==========================================================================
   5b. Curriculum Subjects, Facilities & Academic Departments CRUD
   ========================================================================== */

// --- Curriculum Subjects ---
async function filterSubjectsTable() {
    const search = (document.getElementById('searchSubjectInput')?.value || '').trim().toLowerCase();
    const dept = document.getElementById('filterSubjectDept')?.value || 'all';
    const sem = document.getElementById('filterSubjectSem')?.value || 'all';
    const type = document.getElementById('filterSubjectType')?.value || 'all';

    let url = `/api/subjects?department_id=${encodeURIComponent(dept)}`;
    if (sem !== 'all') url += `&semester=${encodeURIComponent(sem)}`;

    const res = await apiCall(url);
    if (!res.success) return;

    const tbody = document.getElementById('subjectsTableBody');
    if (!tbody) return;

    let subjects = res.subjects || [];
    if (type !== 'all') {
        subjects = subjects.filter(s => s.type === type);
    }
    if (search) {
        subjects = subjects.filter(s =>
            (s.name || '').toLowerCase().includes(search) ||
            (s.code || '').toLowerCase().includes(search) ||
            (s.teacher_name || '').toLowerCase().includes(search) ||
            (s.department_code || '').toLowerCase().includes(search)
        );
    }

    if (subjects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No curriculum subjects matching the filter criteria.</td></tr>';
        return;
    }

    tbody.innerHTML = subjects.map(s => {
        const isLab = s.type === 'lab';
        return `
            <tr>
                <td><strong>${s.name}</strong></td>
                <td><span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:700;">${s.code}</span></td>
                <td><span class="badge-pill neutral">${s.department_code || 'GEN'}</span></td>
                <td>Year ${s.year}, Sem ${s.semester}</td>
                <td><span class="badge ${isLab ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-primary-subtle text-primary border border-primary-subtle'}">${isLab ? 'Laboratory' : 'Theory Lecture'}</span></td>
                <td><strong>${s.hours_per_week || 4} hrs</strong> / week</td>
                <td>${s.teacher_name ? `<span class="fw-semibold text-dark">${s.teacher_name}</span>` : '<span class="text-muted fst-italic">Unassigned</span>'}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteSubjectRecord('${s.id}')" title="Delete Curriculum Subject">
                        <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    initLucideIcons();
}

async function saveSubjectSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('modalSubName')?.value.trim();
    const code = document.getElementById('modalSubCode')?.value.trim();
    const dept = document.getElementById('modalSubDept')?.value;
    const year = document.getElementById('modalSubYear')?.value;
    const sem = document.getElementById('modalSubSem')?.value;
    const hours = document.getElementById('modalSubHours')?.value;
    const type = document.getElementById('modalSubType')?.value;
    const teacherId = document.getElementById('modalSubTeacher')?.value || null;

    const res = await apiCall('/api/subjects', 'POST', {
        name, code, department_id: dept, year, semester: sem,
        hours_per_week: hours, type, teacher_id: teacherId
    });

    if (res.success) {
        showToast('Curriculum subject added successfully.', 'success');
        closeModal('modalAddSubject');
        document.getElementById('modalSubName').value = '';
        document.getElementById('modalSubCode').value = '';
        await initAdminData();
        filterSubjectsTable();
        loadDashboardStats();
    } else {
        showToast(res.message || 'Failed to add subject.', 'danger');
    }
}

async function deleteSubjectRecord(id) {
    if (!confirm('Are you sure you want to remove this curriculum subject?')) return;
    const res = await apiCall(`/api/subjects/${id}`, 'DELETE');
    if (res.success) {
        showToast('Curriculum subject removed.', 'info');
        await initAdminData();
        filterSubjectsTable();
        loadDashboardStats();
    } else {
        showToast(res.message || 'Failed to delete subject.', 'danger');
    }
}

// --- Classrooms & Specialized Labs ---
async function filterFacilitiesTable() {
    const search = (document.getElementById('searchFacilityInput')?.value || '').trim().toLowerCase();
    const type = document.getElementById('filterFacilityType')?.value || 'all';

    const res = await apiCall('/api/classrooms');
    if (!res.success) return;

    const tbody = document.getElementById('facilitiesTableBody');
    if (!tbody) return;

    let rooms = res.classrooms || [];
    if (type !== 'all') {
        rooms = rooms.filter(r => r.type === type);
    }
    if (search) {
        rooms = rooms.filter(r =>
            (r.name || '').toLowerCase().includes(search) ||
            (r.building || '').toLowerCase().includes(search)
        );
    }

    if (rooms.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No facility records found matching criteria.</td></tr>';
        return;
    }

    tbody.innerHTML = rooms.map(r => {
        const isLab = r.type === 'lab';
        return `
            <tr>
                <td><strong>${r.name}</strong></td>
                <td><span class="badge ${isLab ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-primary-subtle text-primary border border-primary-subtle'}">${isLab ? 'Specialized Lab' : 'Lecture Hall / Classroom'}</span></td>
                <td><strong>${r.capacity}</strong> Seats</td>
                <td>${r.building || 'Main Campus'}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteFacilityRecord('${r.id}')" title="Delete Facility">
                        <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    initLucideIcons();
}

async function saveClassroomSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('modalRoomName')?.value.trim();
    const type = document.getElementById('modalRoomType')?.value;
    const capacity = document.getElementById('modalRoomCap')?.value;
    const building = document.getElementById('modalRoomBld')?.value.trim();

    const res = await apiCall('/api/classrooms', 'POST', {
        name, type, capacity, building
    });

    if (res.success) {
        showToast('Facility registered successfully.', 'success');
        closeModal('modalAddClassroom');
        document.getElementById('modalRoomName').value = '';
        await initAdminData();
        filterFacilitiesTable();
        loadDashboardStats();
    } else {
        showToast(res.message || 'Failed to add facility.', 'danger');
    }
}

async function deleteFacilityRecord(id) {
    if (!confirm('Remove this facility from the campus directory?')) return;
    const res = await apiCall(`/api/classrooms/${id}`, 'DELETE');
    if (res.success) {
        showToast('Facility removed.', 'info');
        await initAdminData();
        filterFacilitiesTable();
        loadDashboardStats();
    } else {
        showToast(res.message || 'Failed to delete facility.', 'danger');
    }
}

// --- Academic Departments ---
async function filterDepartmentsTable() {
    const search = (document.getElementById('searchDeptInput')?.value || '').trim().toLowerCase();

    const res = await apiCall('/api/departments');
    if (!res.success) return;

    const tbody = document.getElementById('departmentsTableBody');
    if (!tbody) return;

    let depts = res.departments || [];
    if (search) {
        depts = depts.filter(d =>
            (d.name || '').toLowerCase().includes(search) ||
            (d.code || '').toLowerCase().includes(search)
        );
    }

    if (depts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No departments matching the search term.</td></tr>';
        return;
    }

    tbody.innerHTML = depts.map(d => `
        <tr>
            <td><strong>${d.name}</strong></td>
            <td><span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:700; font-size: 0.8rem;">${d.code}</span></td>
            <td><span class="badge bg-light text-dark border"><i data-lucide="users" style="width:12px;height:12px;display:inline-block;"></i> ${d.faculty_count || 0} Faculty</span></td>
            <td><span class="badge bg-light text-dark border"><i data-lucide="book" style="width:12px;height:12px;display:inline-block;"></i> ${d.subjects_count || 0} Courses</span></td>
            <td><span class="badge bg-light text-dark border"><i data-lucide="graduation-cap" style="width:12px;height:12px;display:inline-block;"></i> ${d.students_count || 0} Students</span></td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-danger" onclick="deleteDepartmentRecord('${d.id}')" title="Delete Academic Department">
                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                </button>
            </td>
        </tr>
    `).join('');

    initLucideIcons();
}

async function saveDepartmentSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('modalDeptName')?.value.trim();
    const code = document.getElementById('modalDeptCode')?.value.trim();

    const res = await apiCall('/api/departments', 'POST', {
        name, code
    });

    if (res.success) {
        showToast('Department registered successfully.', 'success');
        closeModal('modalAddDepartment');
        document.getElementById('modalDeptName').value = '';
        document.getElementById('modalDeptCode').value = '';
        await initAdminData();
        filterDepartmentsTable();
        loadDashboardStats();
    } else {
        showToast(res.message || 'Failed to register department.', 'danger');
    }
}

async function deleteDepartmentRecord(id) {
    if (!confirm('Are you sure you want to remove this academic department? This may affect linked courses.')) return;
    const res = await apiCall(`/api/departments/${id}`, 'DELETE');
    if (res.success) {
        showToast('Department deleted.', 'info');
        await initAdminData();
        filterDepartmentsTable();
        loadDashboardStats();
    } else {
        showToast(res.message || 'Failed to delete department.', 'danger');
    }
}

/* ==========================================================================
   6. Events, Lost-Class Recovery & Activities
   ========================================================================== */

async function loadEventsData() {
    const [evRes, extRes] = await Promise.all([
        apiCall('/api/events'),
        apiCall('/api/extra-classes')
    ]);

    if (evRes.success) {
        const tbody = document.getElementById('eventsTableBody');
        if (tbody) {
            tbody.innerHTML = evRes.events.map(ev => `
                <tr>
                    <td><strong>${ev.title}</strong><br><small class="text-muted">${ev.description || ''}</small></td>
                    <td><span class="badge-pill ${ev.event_type === 'holiday' ? 'danger' : 'warning'}">${ev.event_type.toUpperCase()}</span></td>
                    <td>${ev.event_date} (${ev.start_time} - ${ev.end_time})</td>
                    <td>${ev.department_code || 'All Depts'}</td>
                    <td><strong class="text-danger">${ev.periods_lost} periods</strong></td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteEventRecord('${ev.id}')">
                            <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    }

    if (extRes.success) {
        document.getElementById('metricLostClasses').textContent = extRes.metrics.total_lost;
        document.getElementById('metricScheduledRecovery').textContent = extRes.metrics.replacement_scheduled;
        document.getElementById('metricCompletedRecovery').textContent = extRes.metrics.replacement_completed;
        document.getElementById('metricRemainingRecovery').textContent = extRes.metrics.remaining_to_recover;

        const tbody = document.getElementById('extraClassesTableBody');
        if (tbody) {
            tbody.innerHTML = extRes.extra_classes.map(ec => `
                <tr>
                    <td><strong>${ec.subject_code}</strong> - ${ec.subject_name}</td>
                    <td>${ec.teacher_name}</td>
                    <td>${ec.dept_code} Y${ec.year}S${ec.semester}</td>
                    <td>${ec.replacement_date}</td>
                    <td>Period ${ec.period}</td>
                    <td>${ec.classroom_name}</td>
                    <td>
                        <span class="badge-pill ${ec.status === 'completed' ? 'success' : 'primary'}">
                            ${ec.status.toUpperCase()}
                        </span>
                    </td>
                    <td class="text-end">
                        ${ec.status === 'scheduled' ? `
                            <button class="btn btn-sm btn-outline-success" onclick="toggleExtraClassStatus('${ec.id}', 'completed')">
                                <i data-lucide="check" style="width: 14px; height: 14px;"></i> Complete
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');
        }
    }

    initLucideIcons();
}

async function saveEventSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('evTitle').value;
    const event_type = document.getElementById('evType').value;
    const event_date = document.getElementById('evDate').value;
    const affected_department_id = document.getElementById('evDept').value;
    const periods_lost = document.getElementById('evPeriodsLost').value;
    const description = document.getElementById('evDesc').value;

    const res = await apiCall('/api/events', 'POST', {
        title, event_type, event_date, affected_department_id, periods_lost, description
    });

    if (res.success) {
        showToast('Event logged and lost periods recorded.', 'success');
        closeModal('modalNewEvent');
        loadEventsData();
        if (adminCalendarInstance) adminCalendarInstance.refetchEvents();
    }
}

async function saveExtraClassSubmit(e) {
    e.preventDefault();
    const subject_id = document.getElementById('extraSubjectSelect').value;
    const teacher_id = document.getElementById('extraTeacherSelect').value;
    const replacement_date = document.getElementById('extraDate').value;
    const period = document.getElementById('extraPeriod').value;
    const classroom_id = document.getElementById('extraRoomSelect').value;

    const res = await apiCall('/api/extra-classes', 'POST', {
        subject_id, teacher_id, replacement_date, period, classroom_id
    });

    if (res.success) {
        showToast('Extra class scheduled for recovery.', 'success');
        closeModal('modalScheduleExtraClass');
        loadEventsData();
        if (adminCalendarInstance) adminCalendarInstance.refetchEvents();
    }
}

async function toggleExtraClassStatus(id, newStatus) {
    const res = await apiCall(`/api/extra-classes/${id}/status`, 'PUT', { status: newStatus });
    if (res.success) {
        showToast('Class recovery marked completed.', 'success');
        loadEventsData();
    }
}

function autoFillExtraTeacher() {
    const subSelect = document.getElementById('extraSubjectSelect');
    const opt = subSelect.options[subSelect.selectedIndex];
    const defaultTch = opt.getAttribute('data-teacher');
    if (defaultTch && defaultTch !== 'null') {
        document.getElementById('extraTeacherSelect').value = defaultTch;
    }
}

async function loadActivitiesData() {
    const res = await apiCall('/api/activities');
    if (!res.success) return;

    const tbody = document.getElementById('activitiesTableBody');
    if (!tbody) return;

    tbody.innerHTML = res.activities.map(act => `
        <tr>
            <td><strong>${act.name}</strong></td>
            <td><span class="badge-pill success">${act.activity_type.toUpperCase()}</span></td>
            <td>${act.day}, Period ${act.period}</td>
            <td>${act.department_code || 'All Cohorts'}</td>
            <td>${act.coordinator_name || 'Assigned Coordinator'}</td>
            <td>${act.venue || 'Campus Facility'}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-danger" onclick="deleteActivityRecord('${act.id}')">
                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                </button>
            </td>
        </tr>
    `).join('');

    initLucideIcons();
}

async function saveActivitySubmit(e) {
    e.preventDefault();
    const name = document.getElementById('actName').value;
    const activity_type = document.getElementById('actType').value;
    const day = document.getElementById('actDay').value;
    const period = document.getElementById('actPeriod').value;
    const venue = document.getElementById('actVenue').value;

    const res = await apiCall('/api/activities', 'POST', {
        name, activity_type, day, period, venue
    });

    if (res.success) {
        showToast('Activity period registered and protected.', 'success');
        closeModal('modalNewActivity');
        loadActivitiesData();
    }
}

async function deleteActivityRecord(id) {
    if (!confirm('Remove activity period?')) return;
    const res = await apiCall(`/api/activities/${id}`, 'DELETE');
    if (res.success) {
        showToast('Activity period removed.', 'info');
        loadActivitiesData();
    }
}

/* ==========================================================================
   7. Mutual Swaps Audit & Announcements
   ========================================================================== */

async function loadSwapsData() {
    const res = await apiCall('/api/swaps');
    if (!res.success) return;

    const tbodySwaps = document.getElementById('adminSwapsTableBody');
    if (tbodySwaps) {
        tbodySwaps.innerHTML = res.swaps.map(sw => {
            let badge = '<span class="badge-pill warning">Pending Consent</span>';
            if (sw.status === 'accepted') badge = '<span class="badge-pill success">Mutual Accepted</span>';
            else if (sw.status === 'rejected') badge = '<span class="badge-pill danger">Declined</span>';

            return `
                <tr>
                    <td><strong>${sw.sender_name}</strong></td>
                    <td><strong>${sw.receiver_name}</strong></td>
                    <td>${sw.sender_day} P${sw.sender_period} (${sw.sender_subject_code || 'Class'})</td>
                    <td>${sw.receiver_day} P${sw.receiver_period} (${sw.receiver_subject_code || 'Class'})</td>
                    <td class="text-truncate" style="max-width: 200px;">${sw.reason}</td>
                    <td>${badge}</td>
                    <td>${formatDate(sw.created_at)}</td>
                </tr>
            `;
        }).join('');
    }

    const tbodyHistory = document.getElementById('swapHistoryTableBody');
    if (tbodyHistory) {
        tbodyHistory.innerHTML = res.history.map(h => `
            <tr>
                <td>${formatDate(h.executed_at)}</td>
                <td>${h.sender_name}</td>
                <td>${h.receiver_name}</td>
                <td>${h.details}</td>
            </tr>
        `).join('');
    }
}

async function loadAnnouncementsData() {
    const res = await apiCall('/api/announcements');
    if (!res.success) return;

    const tbody = document.getElementById('announcementsTableBody');
    if (!tbody) return;

    tbody.innerHTML = res.announcements.map(ann => `
        <tr>
            <td><strong>${ann.title}</strong></td>
            <td><span class="badge-pill neutral">${ann.target_department === 'all' ? 'Campus Wide' : ann.target_department}</span></td>
            <td>${ann.content.substring(0, 90)}...</td>
            <td>${formatDate(ann.created_at)}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-danger" onclick="deleteAnnouncementRecord('${ann.id}')">
                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                </button>
            </td>
        </tr>
    `).join('');

    initLucideIcons();
}

async function saveAnnouncementSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('annTitleInput').value;
    const target_department = document.getElementById('annTargetDeptInput').value;
    const content = document.getElementById('annContentInput').value;

    const res = await apiCall('/api/announcements', 'POST', {
        title, target_department, content
    });

    if (res.success) {
        showToast('Announcement published successfully.', 'success');
        closeModal('modalNewAnnouncement');
        loadAnnouncementsData();
        loadDashboardStats();
    }
}

async function deleteAnnouncementRecord(id) {
    if (!confirm('Delete announcement?')) return;
    const res = await apiCall(`/api/announcements/${id}`, 'DELETE');
    if (res.success) {
        showToast('Announcement removed.', 'info');
        loadAnnouncementsData();
        loadDashboardStats();
    }
}

/* ==========================================================================
   Utility Helpers & Modal Triggers
   ========================================================================== */

function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el && window.bootstrap) {
        const modal = bootstrap.Modal.getOrCreateInstance(el);
        modal.show();
    }
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el && window.bootstrap) {
        const modal = bootstrap.Modal.getInstance(el);
        if (modal) modal.hide();
    }
}

// Hook section switching
const originalShowSection = window.showBentoSection;
window.showBentoSection = function(sectionId) {
    originalShowSection(sectionId);
    if (sectionId === 'timetables') loadSelectedTimetable();
    else if (sectionId === 'analytics') loadAnalyticsData();
    else if (sectionId === 'calendar' && adminCalendarInstance) {
        setTimeout(() => adminCalendarInstance.render(), 100);
    }
    else if (sectionId === 'faculty') filterTeachersTable();
    else if (sectionId === 'students') filterStudentsTable();
    else if (sectionId === 'curriculum') filterSubjectsTable();
    else if (sectionId === 'facilities') filterFacilitiesTable();
    else if (sectionId === 'departments') filterDepartmentsTable();
    else if (sectionId === 'events') loadEventsData();
    else if (sectionId === 'activities') loadActivitiesData();
    else if (sectionId === 'swaps') loadSwapsData();
    else if (sectionId === 'announcements') loadAnnouncementsData();
};
