/**
 * TimetablePro - Faculty Instruction & Coordination Controller
 * Handles personal timetable rendering, mutual class swapping,
 * syllabus topic progress tracking, assignment creation, and personal calendar.
 */

let myTeacherProfile = null;
let myAssignedSubjects = [];
let myTimetableSlots = [];
let teacherCalendarInstance = null;

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const PERIODS = [
    { number: 1, start: "09:00", end: "09:50" },
    { number: 2, start: "09:50", end: "10:40" },
    { number: 3, start: "10:40", end: "11:30" },
    { number: 4, start: "11:45", end: "12:35" },
    { number: 5, start: "12:35", end: "01:25" },
    { number: 6, start: "02:00", end: "02:50" },
    { number: 7, start: "02:50", end: "03:40" },
    { number: 8, start: "03:40", end: "04:30" }
];

document.addEventListener('DOMContentLoaded', async () => {
    await initTeacherData();
    initTeacherCalendar();
    loadTeacherDashboardOverview();
});

let allDepartments = [];

async function initTeacherData() {
    const meRes = await apiCall('/api/auth/me');
    if (meRes.success) {
        myTeacherProfile = meRes.user;
    }

    const [subRes, tDetailRes, deptRes] = await Promise.all([
        apiCall('/api/subjects'),
        apiCall(`/api/teachers/${myTeacherProfile.id}`),
        apiCall('/api/departments')
    ]);

    if (subRes.success) {
        myAssignedSubjects = subRes.subjects.filter(s => s.teacher_id === myTeacherProfile.id);
    }
    if (tDetailRes.success) {
        myTimetableSlots = tDetailRes.slots || [];
    }
    if (deptRes.success) {
        allDepartments = deptRes.departments || [];
    }

    populateTeacherDropdowns();
}

function populateTeacherDropdowns() {
    // Populate departments for Full Timetable view
    const fullDeptSelect = document.getElementById('fullTtDept');
    if (fullDeptSelect && allDepartments.length > 0) {
        fullDeptSelect.innerHTML = allDepartments.map(d => `
            <option value="${d.id}" ${myTeacherProfile && myTeacherProfile.department_id === d.id ? 'selected' : ''}>
                ${d.name} (${d.code})
            </option>
        `).join('');
        loadTeacherFullTimetable();
    }
    // Populate subjects for syllabus
    const sylSelect = document.getElementById('syllabusSubjectSelect');
    if (sylSelect) {
        sylSelect.innerHTML = myAssignedSubjects.map(s => `
            <option value="${s.id}">${s.code} - ${s.name} (${s.department_code})</option>
        `).join('');
        if (myAssignedSubjects.length > 0) {
            loadSyllabusForSelectedSubject();
        }
    }

    // Populate subjects for assignments
    const asnSelect = document.getElementById('asnSubjectSelect');
    if (asnSelect) {
        asnSelect.innerHTML = myAssignedSubjects.map(s => `
            <option value="${s.id}">${s.code} - ${s.name} (${s.department_code})</option>
        `).join('');
    }

    // Populate my classes for swap offer
    const swapSender = document.getElementById('swapSenderSlotSelect');
    if (swapSender) {
        swapSender.innerHTML = myTimetableSlots.map(s => `
            <option value="${s.day}|${s.period}|${s.subject_id}">
                ${s.day} Period ${s.period} (${s.subject_code || 'Class'}) - ${s.classroom_name || 'Room'}
            </option>
        `).join('');
    }
}

/* ==========================================================================
   1. Dashboard Overview & Today's Timeline
   ========================================================================== */

function getDayOfWeekName() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[new Date().getDay()];
}

async function loadTeacherDashboardOverview() {
    document.getElementById('teacherWeeklyPeriods').textContent = myTimetableSlots.length;
    document.getElementById('teacherSubjectCount').textContent = myAssignedSubjects.length;

    const todayDay = getDayOfWeekName();
    const dayLabel = document.getElementById('teacherTodayDayLabel');
    const dateLabel = document.getElementById('teacherTodayDate');
    if (dayLabel) dayLabel.textContent = todayDay;
    if (dateLabel) dateLabel.textContent = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });

    // Filter today's slots
    const todaySlots = myTimetableSlots.filter(s => s.day === todayDay);
    todaySlots.sort((a, b) => a.period - b.period);
    document.getElementById('teacherTodayCount').textContent = todaySlots.length;

    const timeline = document.getElementById('teacherTodayTimeline');
    if (timeline) {
        if (todayDay === 'Sunday') {
            timeline.innerHTML = '<div class="text-muted text-center py-4" style="font-size: 0.85rem;">Sunday is a campus rest day. No teaching periods scheduled.</div>';
        } else if (todaySlots.length === 0) {
            timeline.innerHTML = `<div class="text-muted text-center py-4" style="font-size: 0.85rem;">You have no classes scheduled for today (${todayDay}).</div>`;
        } else {
            timeline.innerHTML = todaySlots.map(s => {
                const pInfo = PERIODS.find(p => p.number == s.period) || { start: '', end: '' };
                const isLab = s.slot_type === 'lab';
                return `
                    <div class="p-3 rounded border bg-white d-flex justify-content-between align-items-center" style="border-left: 4px solid ${isLab ? 'var(--success)' : 'var(--primary)'} !important;">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge-pill ${isLab ? 'success' : 'primary'}">Period ${s.period}</span>
                                <span class="text-muted" style="font-size: 0.75rem;">${pInfo.start} - ${pInfo.end}</span>
                            </div>
                            <strong style="font-size: 0.95rem; color: var(--slate-900);">${s.subject_name || 'Class'} (${s.subject_code || ''})</strong>
                            <div class="text-secondary" style="font-size: 0.8rem; margin-top: 0.2rem;">
                                <span>Room: <strong>${s.classroom_name || 'TBD'}</strong></span> |
                                <span>Cohort: <strong>${s.dept_code} Year ${s.year} Sem ${s.semester}</strong></span>
                            </div>
                        </div>
                        <span class="badge-pill neutral">${isLab ? 'Laboratory' : 'Theory Lecture'}</span>
                    </div>
                `;
            }).join('');
        }
    }

    // Load pending incoming swaps count
    const swapRes = await apiCall('/api/swaps');
    if (swapRes.success) {
        const pendingCount = (swapRes.incoming || []).filter(s => s.status === 'pending').length;
        document.getElementById('teacherPendingSwaps').textContent = pendingCount;
    }

    // Load notices preview
    const annRes = await apiCall('/api/announcements');
    const annPreview = document.getElementById('teacherAnnouncementsPreview');
    if (annPreview && annRes.success) {
        if (annRes.announcements.length > 0) {
            annPreview.innerHTML = annRes.announcements.slice(0, 3).map(a => `
                <div class="mb-2 pb-2 border-bottom">
                    <strong class="text-dark">${a.title}</strong>
                    <div class="text-muted" style="font-size: 0.72rem;">${a.content.substring(0, 80)}...</div>
                </div>
            `).join('');
        } else {
            annPreview.innerHTML = '<div class="text-muted">No notices at this time.</div>';
        }
    }

    initLucideIcons();
}

/* ==========================================================================
   2. Master Weekly Routine Grid
   ========================================================================== */

function loadTeacherWeeklyTimetable() {
    const container = document.getElementById('teacherTimetableContainer');
    if (!container) return;

    // Map my slots
    const slotMap = {};
    myTimetableSlots.forEach(s => {
        slotMap[`${s.day}_${s.period}`] = s;
    });

    let html = `
        <table class="timetable-table">
            <thead>
                <tr>
                    <th class="time-col">Period / Time</th>
                    ${DAYS.map(d => `<th>${d}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    PERIODS.forEach(p => {
        if (p.number === 4) {
            html += `
                <tr class="break-interval-row">
                    <td>11:30 - 11:45</td>
                    <td colspan="6">Morning Refreshment Break</td>
                </tr>
            `;
        }
        if (p.number === 6) {
            html += `
                <tr class="break-interval-row">
                    <td>01:25 - 02:00</td>
                    <td colspan="6">Lunch Break Interval</td>
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

        DAYS.forEach(d => {
            const slot = slotMap[`${d}_${p.number}`];
            if (slot) {
                const isLab = slot.slot_type === 'lab';
                html += `
                    <td>
                        <div class="period-cell ${isLab ? 'cell-lab' : ''}" style="cursor: default;">
                            <span class="slot-code">${slot.subject_code || 'CLASS'}</span>
                            <span class="slot-name">${slot.subject_name || ''}</span>
                            <span class="slot-meta">${slot.dept_code} Y${slot.year}S${slot.semester}</span>
                            <span class="slot-meta">${slot.classroom_name || 'Room'}</span>
                        </div>
                    </td>
                `;
            } else {
                html += `
                    <td>
                        <div class="empty-slot" style="cursor: default; border: none; background: transparent;">
                            <span style="color: var(--slate-300);">-</span>
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

/* ==========================================================================
   2B. Institutional / Cohort Full Master Timetable Grid
   ========================================================================== */

async function loadTeacherFullTimetable() {
    const container = document.getElementById('teacherFullTimetableContainer');
    if (!container) return;

    const deptId = document.getElementById('fullTtDept')?.value || (myTeacherProfile ? myTeacherProfile.department_id : 'dept_1');
    const sem = parseInt(document.getElementById('fullTtSem')?.value || '5');
    const sec = document.getElementById('fullTtSection')?.value || 'A';
    const year = Math.ceil(sem / 2);

    container.innerHTML = `
        <div class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm me-2"></span> Loading official routine...
        </div>
    `;

    const res = await apiCall(`/api/timetables?department_id=${deptId}&year=${year}&semester=${sem}&section=${sec}`);
    if (!res.success || !res.timetable) {
        container.innerHTML = `
            <div class="empty-state-box text-center p-4" style="background: white; border-radius: var(--radius-md); border: 1px dashed var(--slate-300);">
                <i data-lucide="calendar-x" style="width: 40px; height: 40px; color: var(--slate-400); margin-bottom: 0.5rem;"></i>
                <h5 class="fw-semibold mb-1" style="font-size: 0.95rem;">No Timetable Scheduled Yet</h5>
                <p class="text-muted mb-0" style="font-size: 0.8rem;">No official class routine has been published for Semester ${sem} Section ${sec}.</p>
            </div>
        `;
        initLucideIcons();
        return;
    }

    const slots = res.slots || [];
    const periodsConfig = res.periods_config || PERIODS;
    const daysConfig = res.days_config || DAYS;

    const slotMap = {};
    slots.forEach(s => {
        slotMap[`${s.day}_${s.period}`] = s;
    });

    let html = `
        <div class="d-flex justify-content-between align-items-center mb-2 px-1">
            <span class="badge bg-indigo-subtle text-indigo" style="font-size: 0.8rem; font-weight: 600;">
                ${res.timetable.department_name || 'CSE'} - Semester ${sem} Section ${sec}
            </span>
            <span class="text-muted" style="font-size: 0.75rem;">
                <span class="badge bg-primary me-1" style="font-size: 0.65rem;">My Class</span> = Your scheduled sessions
            </span>
        </div>
        <table class="timetable-table">
            <thead>
                <tr>
                    <th class="time-col">Period / Time</th>
                    ${daysConfig.map(d => `<th>${d}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    periodsConfig.forEach(p => {
        if (p.number === 3 && p.start === "10:45") {
            html += `
                <tr class="break-interval-row">
                    <td>10:30 - 10:45</td>
                    <td colspan="6">Tea Break Interval</td>
                </tr>
            `;
        } else if (p.number === 4 && p.start === "11:45") {
            // standard break 4 if needed
        }
        if (p.number === 5 && p.start === "01:30") {
            html += `
                <tr class="break-interval-row">
                    <td>12:45 - 01:30</td>
                    <td colspan="6">Lunch Break Interval</td>
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

        daysConfig.forEach(d => {
            const slot = slotMap[`${d}_${p.number}`];
            if (slot) {
                const isMyClass = myTeacherProfile && slot.teacher_id === myTeacherProfile.id;
                const isLab = slot.slot_type === 'lab';
                const isActivity = slot.slot_type === 'activity';

                const cellClasses = ['period-cell'];
                if (isLab) cellClasses.push('cell-lab');
                if (isActivity) cellClasses.push('cell-activity');

                const highlightStyle = isMyClass 
                    ? 'border: 2px solid var(--primary); background: #eef2ff !important; box-shadow: 0 0 0 1px var(--primary);' 
                    : 'cursor: default;';

                html += `
                    <td>
                        <div class="${cellClasses.join(' ')}" style="${highlightStyle}">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="slot-code">${slot.subject_code || (isActivity ? 'ACTIVITY' : 'CLASS')}</span>
                                ${isMyClass ? '<span class="badge bg-primary text-white" style="font-size: 0.6rem; padding: 2px 4px;">My Class</span>' : ''}
                            </div>
                            <span class="slot-name">${slot.subject_name || (isActivity ? 'Sports/Cultural' : '')}</span>
                            <span class="slot-meta" style="font-weight: 600; color: ${isMyClass ? 'var(--primary)' : 'inherit'};">
                                <i data-lucide="user" style="width: 11px; height: 11px; display: inline-block;"></i>
                                ${slot.teacher_name || 'Faculty'}
                            </span>
                            <span class="slot-meta">${slot.classroom_name || 'Room'}</span>
                        </div>
                    </td>
                `;
            } else {
                html += `
                    <td>
                        <div class="empty-slot" style="cursor: default; border: none; background: transparent;">
                            <span style="color: var(--slate-300);">-</span>
                        </div>
                    </td>
                `;
            }
        });

        html += `</tr>`;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
    initLucideIcons();
}

/* ==========================================================================
   3. Mutual Class Swaps Workflow (Peer-to-Peer Hub)
   ========================================================================== */

async function loadTeacherSwapsHub() {
    // Populate colleague selector in swap modal
    const tchRes = await apiCall('/api/teachers');
    const recSelect = document.getElementById('swapReceiverTeacherSelect');
    if (recSelect && tchRes.success) {
        recSelect.innerHTML = '<option value="">-- Choose Colleague --</option>' +
            tchRes.teachers.filter(t => t.id !== myTeacherProfile.id).map(t => `
                <option value="${t.id}">${t.name} (${t.department_code || 'Faculty'})</option>
            `).join('');
    }

    const res = await apiCall('/api/swaps');
    if (!res.success) return;

    // 1. Incoming requests
    const tbodyIn = document.getElementById('incomingSwapsTableBody');
    if (tbodyIn) {
        if (!res.incoming || res.incoming.length === 0) {
            tbodyIn.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No incoming swap requests.</td></tr>';
        } else {
            tbodyIn.innerHTML = res.incoming.map(sw => `
                <tr>
                    <td><strong>${sw.sender_name}</strong></td>
                    <td><span class="badge-pill primary">${sw.sender_day} P${sw.sender_period}</span> (${sw.sender_subject_code || 'Class'})</td>
                    <td><span class="badge-pill neutral">${sw.receiver_day} P${sw.receiver_period}</span> (${sw.receiver_subject_code || 'Class'})</td>
                    <td style="min-width: 200px; max-width: 380px;">${sw.reason}</td>
                    <td><span class="badge-pill ${sw.status === 'accepted' ? 'success' : sw.status === 'rejected' ? 'danger' : 'warning'}">${sw.status.toUpperCase()}</span></td>
                    <td class="text-end">
                        ${sw.status === 'pending' ? `
                            <button class="btn btn-sm btn-success me-1" onclick="handleSwapResponse('${sw.id}', 'accept')">
                                <i data-lucide="check" style="width: 14px; height: 14px;"></i> Accept
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="handleSwapResponse('${sw.id}', 'reject')">
                                <i data-lucide="x" style="width: 14px; height: 14px;"></i> Decline
                            </button>
                        ` : '<span class="text-muted" style="font-size: 0.75rem;">Processed</span>'}
                    </td>
                </tr>
            `).join('');
        }
    }

    // 2. Outgoing requests
    const tbodyOut = document.getElementById('outgoingSwapsTableBody');
    if (tbodyOut) {
        if (!res.outgoing || res.outgoing.length === 0) {
            tbodyOut.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No outgoing swap proposals active.</td></tr>';
        } else {
            tbodyOut.innerHTML = res.outgoing.map(sw => `
                <tr>
                    <td><strong>${sw.receiver_name}</strong></td>
                    <td>${sw.sender_day} P${sw.sender_period} (${sw.sender_subject_code || ''})</td>
                    <td>${sw.receiver_day} P${sw.receiver_period} (${sw.receiver_subject_code || ''})</td>
                    <td style="min-width: 200px; max-width: 380px;">${sw.reason}</td>
                    <td><span class="badge-pill ${sw.status === 'accepted' ? 'success' : sw.status === 'rejected' ? 'danger' : 'warning'}">${sw.status.toUpperCase()}</span></td>
                    <td>${formatDate(sw.created_at)}</td>
                </tr>
            `).join('');
        }
    }

    // 3. Swap History
    const tbodyHist = document.getElementById('teacherSwapHistoryTableBody');
    if (tbodyHist) {
        if (!res.history || res.history.length === 0) {
            tbodyHist.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">No completed swaps in history.</td></tr>';
        } else {
            tbodyHist.innerHTML = res.history.map(h => `
                <tr>
                    <td>${formatDate(h.executed_at)}</td>
                    <td>${h.sender_name === myTeacherProfile.name ? h.receiver_name : h.sender_name}</td>
                    <td>${h.details}</td>
                </tr>
            `).join('');
        }
    }

    initLucideIcons();
}

async function loadReceiverClassesForSwap() {
    const receiverId = document.getElementById('swapReceiverTeacherSelect').value;
    const slotSelect = document.getElementById('swapReceiverSlotSelect');
    if (!receiverId) {
        slotSelect.innerHTML = '<option value="">-- Select Colleague first --</option>';
        return;
    }

    slotSelect.innerHTML = '<option value="">Loading classes...</option>';
    const res = await apiCall(`/api/teachers/${receiverId}`);
    if (res.success && res.slots && res.slots.length > 0) {
        slotSelect.innerHTML = res.slots.map(s => `
            <option value="${s.day}|${s.period}|${s.subject_id}">
                ${s.day} Period ${s.period} (${s.subject_code || 'Class'}) - ${s.classroom_name || 'Room'}
            </option>
        `).join('');
    } else {
        slotSelect.innerHTML = '<option value="">No scheduled teaching slots found for this faculty</option>';
    }
}

async function submitSwapProposal(e) {
    e.preventDefault();
    const senderRaw = document.getElementById('swapSenderSlotSelect').value;
    const receiverId = document.getElementById('swapReceiverTeacherSelect').value;
    const receiverRaw = document.getElementById('swapReceiverSlotSelect').value;
    const reason = document.getElementById('swapReasonInput').value.trim();

    if (!senderRaw || !receiverId || !receiverRaw || !reason) {
        showToast('Please select all swap fields and provide justification.', 'warning');
        return;
    }

    const [sDay, sPeriod, sSub] = senderRaw.split('|');
    const [rDay, rPeriod, rSub] = receiverRaw.split('|');

    const res = await apiCall('/api/swaps/request', 'POST', {
        receiver_teacher_id: receiverId,
        sender_day: sDay,
        sender_period: parseInt(sPeriod),
        sender_subject_id: sSub,
        receiver_day: rDay,
        receiver_period: parseInt(rPeriod),
        receiver_subject_id: rSub,
        reason: reason
    });

    if (res.success) {
        showToast('Mutual class exchange request dispatched to colleague.', 'success');
        closeModal('modalInitiateSwap');
        loadTeacherSwapsHub();
        loadTeacherDashboardOverview();
    } else {
        showToast(res.message, 'danger');
    }
}

async function handleSwapResponse(swapId, action) {
    let rejectionReason = null;
    if (action === 'reject') {
        rejectionReason = prompt('Optional: specify a reason for declining this swap proposal:');
    }

    const res = await apiCall('/api/swaps/respond', 'POST', {
        swap_id: swapId,
        action: action,
        rejection_reason: rejectionReason
    });

    if (res.success) {
        showToast(res.message, 'success');
        await initTeacherData();
        loadTeacherSwapsHub();
        loadTeacherDashboardOverview();
        if (teacherCalendarInstance) teacherCalendarInstance.refetchEvents();
    } else {
        showToast(res.message, 'danger');
    }
}

/* ==========================================================================
   4. Syllabus Progress Tracking
   ========================================================================== */

async function loadSyllabusForSelectedSubject() {
    const subId = document.getElementById('syllabusSubjectSelect')?.value;
    if (!subId) return;

    const res = await apiCall(`/api/syllabus/${subId}`);
    if (!res.success) return;

    const stats = res.stats;
    document.getElementById('syllabusProgressBar').style.width = `${stats.completion_pct}%`;
    document.getElementById('syllabusProgressPct').textContent = `${stats.completion_pct}%`;

    const tbody = document.getElementById('syllabusTableBody');
    if (!tbody) return;

    if (!res.topics || res.topics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No syllabus topics recorded yet for this course. Click "Add Syllabus Topic" above to get started.</td></tr>';
        return;
    }

    tbody.innerHTML = res.topics.map(t => {
        const isDone = t.status === 'completed';
        return `
            <tr style="${isDone ? 'background-color: #f8fafc;' : ''}">
                <td>
                    <input type="checkbox" class="form-check-input" ${isDone ? 'checked' : ''} onchange="toggleTopicCompletion('${t.id}')">
                </td>
                <td>
                    <strong class="${isDone ? 'text-decoration-line-through text-muted' : 'text-dark'}">${t.title}</strong>
                </td>
                <td><span class="badge-pill neutral">${t.chapter || 'Module'}</span></td>
                <td><small class="text-muted">${t.completion_date || 'Pending'}</small></td>
                <td><small class="text-secondary">${t.notes || '-'}</small></td>
                <td class="text-end">
                    <span class="badge-pill ${isDone ? 'success' : 'warning'}">${t.status.toUpperCase()}</span>
                </td>
            </tr>
        `;
    }).join('');

    initLucideIcons();
}

async function toggleTopicCompletion(id) {
    const res = await apiCall(`/api/syllabus/${id}/toggle`, 'PUT', {});
    if (res.success) {
        showToast(`Topic marked as ${res.new_status}.`, 'info');
        loadSyllabusForSelectedSubject();
    }
}

async function saveSyllabusTopicSubmit(e) {
    e.preventDefault();
    const subId = document.getElementById('syllabusSubjectSelect').value;
    const title = document.getElementById('topicTitleInput').value.trim();
    const chapter = document.getElementById('topicChapterInput').value.trim();
    const notes = document.getElementById('topicNotesInput').value.trim();

    const res = await apiCall('/api/syllabus', 'POST', {
        subject_id: subId,
        title, chapter, notes
    });

    if (res.success) {
        showToast('Topic added to syllabus curriculum.', 'success');
        closeModal('modalAddTopic');
        document.getElementById('topicTitleInput').value = '';
        loadSyllabusForSelectedSubject();
    } else {
        showToast(res.message, 'danger');
    }
}

/* ==========================================================================
   5. Assignments Management
   ========================================================================== */

async function loadTeacherAssignments() {
    const res = await apiCall('/api/assignments');
    if (!res.success) return;

    const tbody = document.getElementById('teacherAssignmentsTableBody');
    if (!tbody) return;

    if (!res.assignments || res.assignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No assignments published yet.</td></tr>';
        return;
    }

    tbody.innerHTML = res.assignments.map(a => `
        <tr>
            <td><strong>${a.title}</strong><br><small class="text-muted">${a.description || ''}</small></td>
            <td><span class="badge-pill neutral">${a.subject_code} - ${a.subject_name}</span></td>
            <td>${a.issue_date}</td>
            <td><strong class="text-danger">${a.due_date}</strong></td>
            <td><strong>${a.total_submissions || 0} submissions</strong></td>
            <td class="text-end">
                <span class="badge-pill success">Active</span>
            </td>
        </tr>
    `).join('');

    initLucideIcons();
}

async function saveAssignmentSubmit(e) {
    e.preventDefault();
    const sub_id = document.getElementById('asnSubjectSelect').value;
    const title = document.getElementById('asnTitleInput').value.trim();
    const due_date = document.getElementById('asnDueDateInput').value;
    const description = document.getElementById('asnDescInput').value.trim();

    const res = await apiCall('/api/assignments', 'POST', {
        subject_id: sub_id,
        title, due_date, description
    });

    if (res.success) {
        showToast('Assignment published to students.', 'success');
        closeModal('modalNewAssignment');
        loadTeacherAssignments();
    } else {
        showToast(res.message, 'danger');
    }
}

/* ==========================================================================
   6. Personal Calendar (FullCalendar)
   ========================================================================== */

function initTeacherCalendar() {
    const calendarEl = document.getElementById('teacherFullCalendar');
    if (!calendarEl || !window.FullCalendar) return;

    teacherCalendarInstance = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        slotMinTime: '08:30:00',
        slotMaxTime: '17:30:00',
        allDaySlot: false,
        events: '/api/calendar/events',
        eventClick: function(info) {
            alert(`${info.event.title}\nStarts: ${info.event.start.toLocaleTimeString()}`);
        }
    });

    teacherCalendarInstance.render();
}

/* ==========================================================================
   Modal Helpers & Navigation Hooks
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

const originalShowSectionTeacher = window.showBentoSection;
window.showBentoSection = function(sectionId) {
    originalShowSectionTeacher(sectionId);
    if (sectionId === 'timetable') loadTeacherWeeklyTimetable();
    else if (sectionId === 'swaps') loadTeacherSwapsHub();
    else if (sectionId === 'syllabus') loadSyllabusForSelectedSubject();
    else if (sectionId === 'assignments') loadTeacherAssignments();
    else if (sectionId === 'calendar' && teacherCalendarInstance) {
        setTimeout(() => teacherCalendarInstance.render(), 100);
    }
};
