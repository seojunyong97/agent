/**
 * BTC Insight — 프론트엔드 JavaScript
 * 바닐라 JS로 구현 (프레임워크 없음)
 */

// ── 설정 ────────────────────────────────────────────
const API_BASE = "https://agent-8lk2.onrender.com";

let currentConversationId = null;
let currentMessages = [];

// ── 초기화 ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadSummary();
  loadData();
  loadConversations();
});

// ── 탭 전환 ─────────────────────────────────────────
function switchTab(tab) {
  // 버튼 활성화
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });

  // 탭 콘텐츠 전환
  document.getElementById("tabChat").classList.toggle("active", tab === "chat");
  document.getElementById("tabData").classList.toggle("active", tab === "data");
  document.getElementById("tabHistory").classList.toggle("active", tab === "history");

  // 사이드바 요약/대화목록 전환
  document.getElementById("summaryCard").style.display =
    tab === "history" ? "none" : "block";
  document.getElementById("conversationList").style.display =
    tab === "history" ? "block" : "none";

  // 대화 기록 탭이면 목록 새로고침
  if (tab === "history") {
    loadConversations();
  }
  if (tab === "data") {
    loadData();
  }
}

// ── 데이터 요약 ─────────────────────────────────────
async function loadSummary() {
  const el = document.getElementById("summaryContent");
  try {
    const res = await fetch(`${API_BASE}/api/data/summary`);
    if (!res.ok) throw new Error("요약 로드 실패");
    const data = await res.json();

    const trendClass = data.trend.includes("상승")
      ? "up"
      : data.trend.includes("하락")
      ? "down"
      : "";

    el.innerHTML = `
      <div class="summary-item">
        <span class="summary-label">기간</span>
        <span class="summary-value">${data.period}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">데이터 수</span>
        <span class="summary-value">${data.count}개</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">평균</span>
        <span class="summary-value">$${Number(data.metrics.average).toLocaleString()}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">최고</span>
        <span class="summary-value up">$${Number(data.metrics.max).toLocaleString()}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">최저</span>
        <span class="summary-value down">$${Number(data.metrics.min).toLocaleString()}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">트렌드</span>
        <span class="summary-value ${trendClass}">${data.trend}</span>
      </div>
    `;
  } catch (err) {
    el.innerHTML = `<p class="loading-text">⚠️ 요약을 불러올 수 없습니다.<br>서버가 시작 중일 수 있어요.</p>`;
    console.error("Summary error:", err);
  }
}

// ── 채팅 ────────────────────────────────────────────
async function sendMessage() {
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;

  const sendBtn = document.getElementById("sendBtn");

  // 사용자 메시지 표시
  appendMessage("user", message);
  input.value = "";
  sendBtn.disabled = true;

  // 로딩 표시
  const loadingEl = appendMessage("assistant", "");
  loadingEl.querySelector(".message-bubble").innerHTML =
    '<span class="loading-dots">생각하는 중</span>';

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        conversation_id: currentConversationId,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "서버 오류");
    }

    const data = await res.json();
    loadingEl.querySelector(".message-bubble").textContent = data.reply;
    currentConversationId = data.conversation_id;
  } catch (err) {
    loadingEl.querySelector(".message-bubble").textContent =
      `⚠️ 오류: ${err.message}`;
    console.error("Chat error:", err);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function appendMessage(role, content) {
  const container = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `<div class="message-bubble">${escapeHtml(content)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function startNewChat() {
  currentConversationId = null;
  currentMessages = [];
  const container = document.getElementById("chatMessages");
  container.innerHTML = `
    <div class="message assistant">
      <div class="message-bubble">
        새 대화를 시작합니다! 🪙<br>비트코인에 대해 무엇이든 물어보세요.
      </div>
    </div>
  `;
  switchTab("chat");
}

// ── 데이터 관리 (CRUD) ──────────────────────────────
async function loadData() {
  const tbody = document.getElementById("dataBody");
  tbody.innerHTML = '<tr><td colspan="4" class="loading-text">로딩 중...</td></tr>';

  try {
    const res = await fetch(`${API_BASE}/api/data`);
    if (!res.ok) throw new Error("데이터 로드 실패");
    const data = await res.json();

    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="loading-text">데이터가 없습니다.</td></tr>';
      return;
    }

    tbody.innerHTML = data
      .map(
        (item) => `
      <tr>
        <td>${item.date}</td>
        <td>$${Number(item.value).toLocaleString()}</td>
        <td>${item.memo}</td>
        <td>
          <button class="btn-edit" onclick="openEditModal('${item.id}', '${item.date}', ${item.value}, '${item.memo}')">수정</button>
          <button class="btn-delete" onclick="deleteData('${item.id}')">삭제</button>
        </td>
      </tr>
    `
      )
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="loading-text">⚠️ 데이터를 불러올 수 없습니다.</td></tr>`;
    console.error("Data load error:", err);
  }
}

function toggleAddForm() {
  const form = document.getElementById("addForm");
  form.style.display = form.style.display === "none" ? "block" : "none";
}

async function addData() {
  const date = document.getElementById("inputDate").value;
  const value = parseFloat(document.getElementById("inputValue").value);
  const memo = document.getElementById("inputMemo").value;

  if (!date || isNaN(value)) {
    alert("날짜와 가격을 입력해주세요.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, value, memo }),
    });

    if (!res.ok) throw new Error("추가 실패");
    toggleAddForm();
    loadData();
    loadSummary();

    // 입력 초기화
    document.getElementById("inputDate").value = "";
    document.getElementById("inputValue").value = "";
    document.getElementById("inputMemo").value = "";
  } catch (err) {
    alert("데이터 추가에 실패했습니다: " + err.message);
  }
}

function openEditModal(id, date, value, memo) {
  document.getElementById("editId").value = id;
  document.getElementById("editDate").value = date;
  document.getElementById("editValue").value = value;
  document.getElementById("editMemo").value = memo;
  document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("editModal").style.display = "none";
}

async function updateData() {
  const id = document.getElementById("editId").value;
  const date = document.getElementById("editDate").value;
  const value = parseFloat(document.getElementById("editValue").value);
  const memo = document.getElementById("editMemo").value;

  try {
    const res = await fetch(`${API_BASE}/api/data/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, value, memo }),
    });

    if (!res.ok) throw new Error("수정 실패");
    closeEditModal();
    loadData();
    loadSummary();
  } catch (err) {
    alert("수정 실패: " + err.message);
  }
}

async function deleteData(id) {
  if (!confirm("이 데이터를 삭제하시겠습니까?")) return;

  try {
    const res = await fetch(`${API_BASE}/api/data/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("삭제 실패");
    loadData();
    loadSummary();
  } catch (err) {
    alert("삭제 실패: " + err.message);
  }
}

// ── 대화 기록 ───────────────────────────────────────
async function loadConversations() {
  const listEl = document.getElementById("historyList");
  const sideListEl = document.getElementById("convListItems");

  try {
    const res = await fetch(`${API_BASE}/api/conversations`);
    if (!res.ok) throw new Error("대화 목록 로드 실패");
    const convs = await res.json();

    if (convs.length === 0) {
      listEl.innerHTML = '<p class="loading-text">저장된 대화가 없습니다.</p>';
      sideListEl.innerHTML = '<p class="loading-text">대화 없음</p>';
      return;
    }

    // 메인 기록 탭
    listEl.innerHTML = convs
      .map(
        (c) => `
      <div class="history-item">
        <div class="history-info" onclick="loadConversation('${c.id}')">
          <div class="history-title">${escapeHtml(c.title)}</div>
          <div class="history-meta">${c.created_at?.substring(0, 10) || ""} · ${c.message_count}개 메시지</div>
          ${c.preview ? `<div class="history-preview">${escapeHtml(c.preview)}</div>` : ""}
        </div>
        <div class="history-actions">
          <button class="btn-load" onclick="loadConversation('${c.id}')">불러오기</button>
          <button class="btn-delete" onclick="deleteConversation('${c.id}')">삭제</button>
        </div>
      </div>
    `
      )
      .join("");

    // 사이드바 대화 목록
    sideListEl.innerHTML = convs
      .map(
        (c) => `
      <div class="conv-item" onclick="loadConversation('${c.id}')">
        <div class="conv-title">${escapeHtml(c.title)}</div>
        <div class="conv-meta">${c.message_count}개 메시지</div>
      </div>
    `
      )
      .join("");
  } catch (err) {
    listEl.innerHTML = '<p class="loading-text">⚠️ 대화 목록을 불러올 수 없습니다.</p>';
    sideListEl.innerHTML = "";
    console.error("Conversations error:", err);
  }
}

async function loadConversation(convId) {
  try {
    const res = await fetch(`${API_BASE}/api/conversations/${convId}`);
    if (!res.ok) throw new Error("대화 불러오기 실패");
    const conv = await res.json();

    currentConversationId = convId;
    currentMessages = conv.messages || [];

    // 채팅 화면에 메시지 복원
    const container = document.getElementById("chatMessages");
    container.innerHTML = "";

    if (currentMessages.length === 0) {
      container.innerHTML = `
        <div class="message assistant">
          <div class="message-bubble">이전 대화를 불러왔지만 메시지가 없습니다.</div>
        </div>`;
    } else {
      currentMessages.forEach((msg) => {
        appendMessage(msg.role, msg.content);
      });
    }

    // 채팅 탭으로 전환
    switchTab("chat");
  } catch (err) {
    alert("대화를 불러올 수 없습니다: " + err.message);
  }
}

async function deleteConversation(convId) {
  if (!confirm("이 대화를 삭제하시겠습니까?")) return;

  try {
    const res = await fetch(`${API_BASE}/api/conversations/${convId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("삭제 실패");

    if (currentConversationId === convId) {
      startNewChat();
    }
    loadConversations();
  } catch (err) {
    alert("대화 삭제 실패: " + err.message);
  }
}
