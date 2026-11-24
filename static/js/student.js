/**
 * TimetablePro - Student Portal Controller
 * Manages cohort schedule display, weekly timetable rendering,
 * teacher directory search, assignment submissions, and activity routines.
 */

let myProfile = null;
let myTimetable = null;
let mySlots = [];
let mySubjects = [];
let allFaculty = [];

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
    await initStudentPortal();
    loadStudentDashboard();
});

async function initStudentPortal() {
    const meRes = await apiCall('/api/auth/me');
    if (meRes.success) {
        myProfile = meRes.user;
        document.getElementById('studentDeptBadge').textContent = `Department ID: ${myProfile.department_id}`;
        document.getElementById('studentYearSemBadge').textContent = `Year ${myProfile.year} - Sem ${myProfile.semester}`;
        document.getElementById('studentSectionBadge').textContent = `Section ${myProfile.section || 'A'}`;
    }

    const sec = myProfile.section || 'A';
    const [deptRes, ttRes, subRes, tchRes] = await Promise.all([
        apiCall('/api/departments'),
        apiCall(`/api/timetables?department_id=${myProfile.department_id}&year=${myProfile.year}&semester=${myProfile.semester}&section=${encodeURIComponent(sec)}`),
        apiCall(`/api/subjects?department_id=${myProfile.department_id}&year=${myProfile.year}&semester=${myProfile.semester}`),
        apiCall('/api/teachers')
    ]);

    if (deptRes.success) {
        const d = deptRes.departments.find(dept => dept.id === myProfile.department_id);
        if (d) {
            document.getElementById('studentDeptBadge').textContent = `${d.code} - ${d.name}`;
        }
        // Populate teacher search dept filter
        const fDept = document.getElementById('studentFilterTeacherDept');
        if (fDept) {
            fDept.innerHTML = '<option value="all">All Academic Departments</option>' +
                deptRes.departments.map(dept => `<option value="${dept.id}">${dept.code} - ${dept.name}</option>`).join('');
        }
    }

    if (ttRes.success && ttRes.timetable && ttRes.timetable.published) {
        myTimetable = ttRes.timetable;
        mySlots = ttRes.slots || [];
    }

    if (subRes.success) {
        mySubjects = subRes.subjects || [];
        document.getElementById('studentCourseCount').textContent = mySubjects.length;
    }

    if (tchRes.success) {
        allFaculty = tchRes.teachers || [];
    }
}

/* ==========================================================================
   1. Dashboard Overview & Today's Routine
   ========================================================================== */

function getDayOfWeekName() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[new Date().getDay()];
}

function loadStudentDashboard() {
    const today = getDayOfWeekName();
    document.getElementById('studentTodayDayLabel').textContent = today;
    document.getElementById('studentTodayDateFormatted').textContent = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });

    const todaySlots = mySlots.filter(s => s.day === today);
    todaySlots.sort((a, b) => a.period - b.period);
    document.getElementById('studentTodayClassCount').textContent = todaySlots.length;

    const timeline = document.getElementById('studentTodayTimeline');
    if (timeline) {
        if (!myTimetable) {
            timeline.innerHTML = '<div class="text-muted text-center py-4" style="font-size: 0.85rem;">Official timetable has not been published yet for your cohort.</div>';
        } else if (today === 'Sunday') {
            timeline.innerHTML = '<div class="text-muted text-center py-4" style="font-size: 0.85rem;">Happy Sunday! No lectures or laboratory sessions scheduled today.</div>';
        } else if (todaySlots.length === 0) {
            timeline.innerHTML = `<div class="text-muted text-center py-4" style="font-size: 0.85rem;">No classes scheduled for today (${today}). Self-study and project preparation day.</div>`;
        } else {
            timeline.innerHTML = todaySlots.map(s => {
                const pInfo = PERIODS.find(p => p.number == s.period) || { start: '', end: '' };
                const isLab = s.slot_type === 'lab';
                const isAct = s.slot_type === 'activity';

                return `
                    <div class="p-3 rounded border bg-white d-flex justify-content-between align-items-center" style="border-left: 4px solid ${isLab ? 'var(--success)' : isAct ? '#059669' : 'var(--primary)'} !important;">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge-pill ${isLab ? 'success' : isAct ? 'success' : 'primary'}">Period ${s.period}</span>
                                <span class="text-muted" style="font-size: 0.75rem;">${pInfo.start} - ${pInfo.end}</span>
                            </div>
                            <strong style="font-size: 0.95rem; color: var(--slate-900);">${s.subject_name || (isAct ? 'Campus Activity' : 'Class')} (${s.subject_code || ''})</strong>
                            <div class="text-secondary" style="font-size: 0.8rem; margin-top: 0.2rem;">
                                <span>Instructor: <strong>${s.teacher_name || 'TBD'}</strong></span> |
                                <span>Room: <strong>${s.classroom_name || 'TBD'}</strong> (${s.classroom_building || ''})</span>
                            </div>
                        </div>
                        <span class="badge-pill neutral">${isLab ? 'Practical Lab' : isAct ? 'Activity' : 'Theory Lecture'}</span>
                    </div>
                `;
            }).join('');
        }
    }

    // Determine Next Immediate Class
    const nextCard = document.getElementById('studentNextClassCard');
    if (nextCard) {
        if (todaySlots.length > 0) {
            const nextSlot = todaySlots[0];
            const pInfo = PERIODS.find(p => p.number == nextSlot.period) || { start: '', end: '' };
            nextCard.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <div class="badge-pill primary mb-1">Upcoming Today - Period ${nextSlot.period}</div>
                        <h4 style="font-size: 1.05rem; font-weight: 700; color: var(--slate-900); margin: 0;">${nextSlot.subject_name || 'Class'}</h4>
                        <div class="text-muted" style="font-size: 0.75rem;">${nextSlot.subject_code || ''}</div>
                    </div>
                    <div class="text-end">
                        <strong class="text-primary">${pInfo.start}</strong>
                        <div style="font-size: 0.72rem; color: var(--slate-400);">Starts</div>
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: var(--slate-600);">
                    <div>Instructor: <strong>${nextSlot.teacher_name || 'Faculty'}</strong></div>
                    <div>Location: <strong>${nextSlot.classroom_name || 'Classroom'}</strong> (${nextSlot.classroom_building || 'Campus'})</div>
                </div>
            `;
        } else {
            nextCard.innerHTML = `
                <div class="text-center py-2" style="color: var(--slate-500); font-size: 0.85rem;">
                    No upcoming classes remaining on today's schedule.
                </div>
            `;
        }
    }

    loadStudentPendingAssignmentsCount();
    initLucideIcons();
}

async function loadStudentPendingAssignmentsCount() {
    const res = await apiCall('/api/assignments');
    if (res.success && res.assignments) {
        const pending = res.assignments.filter(a => a.my_status !== 'submitted').length;
        document.getElementById('studentPendingAsnCount').textContent = pending;
    }
}

/* ==========================================================================
   2. Master Weekly Timetable Grid
   ========================================================================== */

function loadStudentWeeklyTimetable() {
    const container = document.getElementById('studentTimetableContainer');
    if (!container) return;

    if (!myTimetable) {
        container.innerHTML = `
            <div style="padding: 3.5rem; text-align: center; color: var(--slate-400);">
                <i data-lucide="calendar-off" style="width: 36px; height: 36px; stroke-width: 1.5; margin-bottom: 0.5rem;"></i>
                <div class="fw-bold text-dark">Timetable Not Published</div>
                <div style="font-size: 0.85rem;">The official weekly class routine for your year and semester has not yet been published by the administration.</div>
            </div>
        `;
        initLucideIcons();
        return;
    }

    const slotMap = {};
    mySlots.forEach(s => {
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
                    <td colspan="6">Institutional Lunch Break Interval</td>
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
                const isAct = slot.slot_type === 'activity';

                html += `
                    <td>
                        <div class="period-cell ${isLab ? 'cell-lab' : isAct ? 'cell-activity' : ''}" style="cursor: default;">
                            <span class="slot-code">${slot.subject_code || (isAct ? 'ACTIVITY' : 'CLASS')}</span>
                            <span class="slot-name">${slot.subject_name || (isAct ? 'Sports/Activity' : '')}</span>
                            <span class="slot-meta">${slot.teacher_name ? slot.teacher_name.split(' ').slice(0, 2).join(' ') : 'TBD'}</span>
                            <span class="slot-meta">${slot.classroom_name || 'Room'}</span>
                        </div>
                    </td>
                `;
            } else {
                html += `
                    <td>
                        <div class="empty-slot" style="cursor: default; border: none; background: transparent;">
                            <span style="color: var(--slate-300); font-style: italic;">Free</span>
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
   3. Faculty Directory Search for Students
   ========================================================================== */

async function filterStudentTeachers() {
    const search = (document.getElementById('studentSearchTeacherInput')?.value || '').trim().toLowerCase();
    const dept = document.getElementById('studentFilterTeacherDept')?.value || 'all';

    const res = await apiCall(`/api/teachers?department_id=${dept}&search=${encodeURIComponent(search)}`);
    if (!res.success) return;

    const tbody = document.getElementById('studentTeachersTableBody');
    if (!tbody) return;

    if (!res.teachers || res.teachers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No matching instructors found.</td></tr>';
        return;
    }

    tbody.innerHTML = res.teachers.map(t => {
        const classes = t.classes_taken || [];
        const classesBadges = classes.length > 0 
            ? classes.slice(0, 2).map(c => `
                <span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:600; font-size:0.72rem; padding: 3px 6px;">
                    ${c.subject_code} <small class="text-muted" style="font-size:0.65rem;">(${c.cohort})</small>
                </span>
            `).join(' ') + (classes.length > 2 ? `<span class="badge bg-light text-muted border" style="font-size:0.7rem;">+${classes.length - 2}</span>` : '')
            : '<span class="text-muted" style="font-size:0.78rem;">No active classes</span>';

        return `
            <tr>
                <td><strong>${t.name}</strong></td>
                <td><span class="badge-pill neutral">${t.department_code || 'GEN'}</span></td>
                <td><a href="mailto:${t.email}">${t.email || 'N/A'}</a></td>
                <td>${t.phone || 'N/A'}</td>
                <td>
                    <div class="d-flex flex-wrap gap-1 align-items-center">
                        ${classesBadges}
                    </div>
                </td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-indigo" onclick="viewTeacherFullSchedule('${t.id}', '${encodeURIComponent(t.name)}')">
                        <i data-lucide="calendar" style="width: 14px; height: 14px;"></i> View Schedule
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    initLucideIcons();
}

async function viewTeacherFullSchedule(teacherId, encodedName) {
    const teacherName = decodeURIComponent(encodedName);
    document.getElementById('teacherScheduleModalTitle').textContent = `Teaching Schedule: ${teacherName}`;
    const tbody = document.getElementById('modalTeacherScheduleTableBody');
    tbody.innerHTML = '<tr><td colspan="9" class="text-center py-3">Loading schedule...</td></tr>';

    openModal('modalViewTeacherSchedule');

    const res = await apiCall(`/api/teachers/${teacherId}`);
    if (!res.success) return;

    const slots = res.slots || [];
    const slotMap = {};
    slots.forEach(s => {
        slotMap[`${s.day}_${s.period}`] = s;
    });

    tbody.innerHTML = DAYS.map(d => {
        let row = `<tr><td><strong>${d.substring(0, 3)}</strong></td>`;
        for (let p = 1; p <= 8; p++) {
            const slot = slotMap[`${d}_${p}`];
            if (slot) {
                const isLab = slot.slot_type === 'lab';
                const bg = isLab ? '#d1fae5' : 'var(--primary-light)';
                const fg = isLab ? '#065f46' : 'var(--primary)';
                const sec = slot.section ? ` [Sec ${slot.section}]` : '';
                row += `
                    <td style="background-color: ${bg}; color: ${fg}; font-weight: 600; font-size: 0.75rem;">
                        ${slot.subject_code || 'Class'}<br>
                        <small style="color: var(--slate-600);">${slot.classroom_name || ''}${sec}</small>
                    </td>
                `;
            } else {
                row += `<td style="color: var(--slate-300);">-</td>`;
            }
        }
        row += `</tr>`;
        return row;
    }).join('');
}

/* ==========================================================================
   4. Assignments & Submission Tracking
   ========================================================================== */

async function loadStudentAssignments() {
    const res = await apiCall('/api/assignments');
    if (!res.success) return;

    const tbody = document.getElementById('studentAssignmentsTableBody');
    if (!tbody) return;

    if (!res.assignments || res.assignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No assignments assigned to your class at this time.</td></tr>';
        return;
    }

    tbody.innerHTML = res.assignments.map(a => {
        const isDone = a.my_status === 'submitted';
        return `
            <tr>
                <td><strong>${a.title}</strong><br><small class="text-muted">${a.description || ''}</small></td>
                <td><span class="badge-pill neutral">${a.subject_code}</span></td>
                <td>${a.teacher_name}</td>
                <td><strong class="text-danger">${a.due_date}</strong></td>
                <td>
                    <span class="badge-pill ${isDone ? 'success' : 'warning'}">
                        ${isDone ? 'SUBMITTED' : 'PENDING'}
                    </span>
                    ${a.my_grade ? `<strong class="text-success ms-2">Grade: ${a.my_grade}</strong>` : ''}
                </td>
                <td class="text-end">
                    ${isDone ? `
                        <span class="text-success" style="font-size: 0.8rem;">
                            <i data-lucide="check-check" style="width: 16px; height: 16px; display: inline;"></i> Completed
                        </span>
                    ` : `
                        <button class="btn btn-sm btn-indigo" onclick="openSubmitModal('${a.id}', '${a.title}')">
                            <i data-lucide="upload" style="width: 14px; height: 14px;"></i> Submit
                        </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');

    initLucideIcons();
}

function openSubmitModal(asnId, asnTitle) {
    document.getElementById('submitAsnId').value = asnId;
    document.getElementById('submitAsnTitle').textContent = `Assignment: ${asnTitle}`;
    document.getElementById('submitAsnNotes').value = '';
    openModal('modalSubmitAssignment');
}

async function executeAssignmentSubmission(e) {
    e.preventDefault();
    const asnId = document.getElementById('submitAsnId').value;
    const notes = document.getElementById('submitAsnNotes').value.trim();

    const res = await apiCall(`/api/student/assignments/${asnId}/submit`, 'POST', { notes });
    if (res.success) {
        showToast('Assignment submitted successfully!', 'success');
        closeModal('modalSubmitAssignment');
        loadStudentAssignments();
        loadStudentPendingAssignmentsCount();
    } else {
        showToast(res.message, 'danger');
    }
}

/* ==========================================================================
   5. Sports, Cultural Activities & Announcements
   ========================================================================== */

async function loadStudentActivities() {
    const res = await apiCall('/api/activities');
    if (!res.success) return;

    const tbody = document.getElementById('studentActivitiesTableBody');
    if (!tbody) return;

    if (!res.activities || res.activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No activity periods configured.</td></tr>';
        return;
    }

    tbody.innerHTML = res.activities.map(act => `
        <tr>
            <td><strong>${act.name}</strong></td>
            <td><span class="badge-pill success">${act.activity_type.toUpperCase()}</span></td>
            <td>${act.day}, Period ${act.period}</td>
            <td>${act.venue || 'Campus Facility'}</td>
            <td>${act.coordinator_name || 'Faculty Coordinator'}</td>
        </tr>
    `).join('');

    initLucideIcons();
}

async function loadStudentAnnouncementsList() {
    const res = await apiCall('/api/announcements');
    if (!res.success) return;

    const container = document.getElementById('studentAnnouncementsFullList');
    if (!container) return;

    if (!res.announcements || res.announcements.length === 0) {
        container.innerHTML = '<div class="text-muted text-center py-4">No campus notices posted.</div>';
        return;
    }

    container.innerHTML = res.announcements.map(ann => `
        <div class="p-3 rounded border bg-white shadow-sm">
            <div class="d-flex justify-content-between align-items-center mb-1">
                <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--slate-900); margin: 0;">${ann.title}</h4>
                <span class="badge-pill neutral">${formatDate(ann.created_at)}</span>
            </div>
            <p style="font-size: 0.825rem; color: var(--slate-600); margin-top: 0.5rem; line-height: 1.5;">${ann.content}</p>
        </div>
    `).join('');
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

const originalShowSectionStudent = window.showBentoSection;
window.showBentoSection = function(sectionId) {
    originalShowSectionStudent(sectionId);
    if (sectionId === 'timetable') loadStudentWeeklyTimetable();
    else if (sectionId === 'faculty-search') filterStudentTeachers();
    else if (sectionId === 'assignments') loadStudentAssignments();
    else if (sectionId === 'activities') loadStudentActivities();
    else if (sectionId === 'announcements') loadStudentAnnouncementsList();
};
