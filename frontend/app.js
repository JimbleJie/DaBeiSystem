const API_BASE = window.APP_CONFIG.apiBaseUrl;

const state = {
  products: [],
  inventoryLabels: [],
  inboundDocuments: [],
  outboundDocuments: [],
  editingProductSkuId: null,
  inventorySystem: {
    engine: {},
    labelStats: {}
  },
  lists: {
    products: {
      search: "",
      page: 1,
      pageSize: 10
    },
    inventory: {
      search: "",
      page: 1,
      pageSize: 10
    },
    inboundDocuments: {
      search: "",
      page: 1,
      pageSize: 10
    },
    outboundDocuments: {
      search: "",
      page: 1,
      pageSize: 10
    }
  }
};

const elements = {
  productList: document.querySelector("#productList"),
  productCount: document.querySelector("#productCount"),
  productsSearch: document.querySelector("#productsSearch"),
  productsPageSize: document.querySelector("#productsPageSize"),
  productModal: document.querySelector("#productModal"),
  openProductModalButton: document.querySelector("#openProductModalButton"),
  closeProductModalButton: document.querySelector("#closeProductModalButton"),
  cancelProductButton: document.querySelector("#cancelProductButton"),
  productForm: document.querySelector("#productForm"),
  productNameInput: document.querySelector("#productNameInput"),
  submitProductButton: document.querySelector("#submitProductButton"),
  inventoryList: document.querySelector("#inventoryList"),
  inventoryEngineCards: document.querySelector("#inventoryEngineCards"),
  inventorySearch: document.querySelector("#inventorySearch"),
  inventoryPageSize: document.querySelector("#inventoryPageSize"),
  inboundDocumentList: document.querySelector("#inboundDocumentList"),
  inboundDocumentsSearch: document.querySelector("#inboundDocumentsSearch"),
  inboundDocumentsPageSize: document.querySelector("#inboundDocumentsPageSize"),
  outboundDocumentList: document.querySelector("#outboundDocumentList"),
  outboundDocumentsSearch: document.querySelector("#outboundDocumentsSearch"),
  outboundDocumentsPageSize: document.querySelector("#outboundDocumentsPageSize"),
  messageText: document.querySelector("#messageText"),
  refreshButton: document.querySelector("#refreshButton")
};

async function fetchDashboard() {
  const dashboard = await request("/dashboard");
  Object.assign(state, dashboard);
  render();
}

function render() {
  renderProducts();
  renderInventorySystem();
  renderInventory();
  renderDocuments();
}

function renderProducts() {
  const result = getListResult("products", state.products);
  elements.productCount.textContent = state.products.length;
  elements.productList.innerHTML = result.items.length > 0
    ? result.items.map((product) => `
      <article class="product-management-card">
        <h3>${product.name}</h3>
        <div class="product-management-actions">
          <button class="ghost-button" type="button" data-product-action="edit" data-sku-id="${product.skuId}">编辑</button>
          <button class="danger-button" type="button" data-product-action="delete" data-sku-id="${product.skuId}">删除</button>
        </div>
      </article>
    `).join("")
    : renderEmptySearchState("暂无产品", result.query);
  renderPagination("products", result);
}

function renderInventorySystem() {
  const engine = state.inventorySystem.engine || {};
  const labelStats = state.inventorySystem.labelStats || {};
  const cards = [
    ["库存总量", engine.totalStock || 0],
    ["已剪标出库", labelStats.outbound || 0],
    ["产品数", engine.skuCount || 0]
  ];

  elements.inventoryEngineCards.innerHTML = cards.map(([label, value]) => `
    <article>
      <span>${label}</span>
      <strong>${value}</strong>
    </article>
  `).join("");
}

function renderInventory() {
  const result = getListResult("inventory", getInventoryItems());
  elements.inventoryList.innerHTML = result.items.length > 0
    ? result.items.map((item) => {
    const product = item.product;
    const productCode = product.barcode || product.skuId || product.qrCode || "-";
    const labels = item.labels;
    const labelItems = labels.length > 0
      ? labels.map((label) => renderProductLabel(label)).join("")
      : `<article class="label-card empty-label"><span>暂无标签</span></article>`;

    return `
      <article class="product-card">
        <div class="product-main">
          <div class="product-info">
            <h3>${product.name}</h3>
            <div class="product-field">
              <span>总库存</span>
              <strong>${product.availableStock}</strong>
            </div>
            <div class="product-field">
              <span>商品编码</span>
              <code>${productCode}</code>
            </div>
          </div>
        </div>
        <div class="product-labels">
          <div class="label-row-head">
            <span>单件标签</span>
            <strong>${labels.length}</strong>
          </div>
          <div class="label-row">${labelItems}</div>
        </div>
      </article>
    `;
  }).join("")
    : renderEmptySearchState("暂无库存数据", result.query);
  renderPagination("inventory", result);
}

function renderProductLabel(label) {
  const statusText = label.status === "in_stock" ? "在库，标签未剪" : `已出库，${label.outboundReason}`;
  return `
    <article class="label-card ${label.status}">
      <div class="label-text">
        <strong>${label.labelCode}</strong>
        <span>${label.productName}</span>
        <span>${statusText}</span>
      </div>
      <img src="${createQrImageUrl(label.labelCode)}" alt="${label.labelCode} 二维码">
      <button class="danger-button label-delete-button" type="button" data-label-action="delete" data-label-code="${label.labelCode}">删除</button>
    </article>
  `;
}

function renderDocuments() {
  const inboundResult = getListResult("inboundDocuments", state.inboundDocuments);
  elements.inboundDocumentList.innerHTML = inboundResult.items.length > 0
    ? inboundResult.items.map((document) => `
      <article class="inbound-document-card">
        <div class="document-card-head">
          <div>
            <h3>${document.productName}</h3>
            <span>${document.documentId} · ${formatTime(document.inboundAt)}</span>
          </div>
          <strong>${document.operator}</strong>
        </div>
        <div class="document-fields">
          <span>合格数量：<strong>${document.qualifiedQuantity}</strong></span>
          <span>不合格数量：<strong>${document.rejectedQuantity}</strong></span>
          <span>入库人：<strong>${document.operator}</strong></span>
        </div>
        <div class="document-qr-list">
          ${document.qrCodes.length > 0
            ? document.qrCodes.map((code) => `
              <div class="document-qr-item">
                <code>${code}</code>
                <img src="${createQrImageUrl(code)}" alt="${code} 二维码">
              </div>
            `).join("")
            : "<span>暂无二维码</span>"
          }
        </div>
      </article>
    `).join("")
    : renderEmptySearchState("暂无入库单", inboundResult.query);
  renderPagination("inboundDocuments", inboundResult);

  const outboundResult = getListResult("outboundDocuments", state.outboundDocuments);
  elements.outboundDocumentList.innerHTML = outboundResult.items.length > 0
    ? outboundResult.items.map((document) => `
      <article class="outbound-document-card">
        <div class="document-card-head">
          <div>
            <h3>${document.productName}</h3>
            <span>${document.documentId} · ${formatTime(document.outboundDate)}</span>
          </div>
          <strong>${document.operator}</strong>
        </div>
        <div class="document-fields outbound-document-fields">
          <span>出库渠道：<strong>${document.outboundReason || "-"}</strong></span>
          <span>产品码：<strong><code>${document.productCode}</code></strong></span>
          <span>出库人：<strong>${document.operator}</strong></span>
          <span>出库日期：<strong>${formatTime(document.outboundDate)}</strong></span>
        </div>
      </article>
    `).join("")
    : renderEmptySearchState("暂无出库单", outboundResult.query);
  renderPagination("outboundDocuments", outboundResult);
}

function getInventoryItems() {
  return state.products.map((product) => ({
    product,
    labels: state.inventoryLabels.filter((label) => label.skuId === product.skuId)
  }));
}

function getListResult(listName, items) {
  const listState = state.lists[listName];
  const query = listState.search.trim().toLocaleLowerCase();
  const filteredItems = query
    ? items.filter((item) => itemMatchesQuery(item, query))
    : items;
  const totalPages = Math.max(Math.ceil(filteredItems.length / listState.pageSize), 1);

  if (listState.page > totalPages) {
    listState.page = totalPages;
  }

  const startIndex = (listState.page - 1) * listState.pageSize;
  const pageItems = filteredItems.slice(startIndex, startIndex + listState.pageSize);

  return {
    items: pageItems,
    query,
    currentPage: listState.page,
    pageSize: listState.pageSize,
    totalItems: filteredItems.length,
    totalSourceItems: items.length,
    totalPages,
    startItem: filteredItems.length > 0 ? startIndex + 1 : 0,
    endItem: Math.min(startIndex + listState.pageSize, filteredItems.length)
  };
}

function itemMatchesQuery(value, query) {
  if (value === null || value === undefined) {
    return false;
  }

  if (Array.isArray(value)) {
    return value.some((item) => itemMatchesQuery(item, query));
  }

  if (typeof value === "object") {
    return Object.values(value).some((item) => itemMatchesQuery(item, query));
  }

  return String(value).toLocaleLowerCase().includes(query);
}

function renderEmptySearchState(emptyText, query) {
  return `<article class="empty-state">${query ? "未找到匹配结果" : emptyText}</article>`;
}

function renderPagination(listName, result) {
  const pagination = document.querySelector(`[data-list-pagination="${listName}"]`);
  if (!pagination) {
    return;
  }

  pagination.innerHTML = `
    <div class="pagination-summary">
      共 ${result.totalItems} 条${result.query ? `，筛选自 ${result.totalSourceItems} 条` : ""}，显示 ${result.startItem}-${result.endItem}
    </div>
    <div class="pagination-actions">
      <button class="ghost-button" type="button" data-page-action="prev" ${result.currentPage <= 1 ? "disabled" : ""}>上一页</button>
      <span>${result.currentPage} / ${result.totalPages}</span>
      <button class="ghost-button" type="button" data-page-action="next" ${result.currentPage >= result.totalPages ? "disabled" : ""}>下一页</button>
    </div>
  `;

  pagination.querySelector("[data-page-action='prev']").addEventListener("click", () => {
    changePage(listName, state.lists[listName].page - 1);
  });
  pagination.querySelector("[data-page-action='next']").addEventListener("click", () => {
    changePage(listName, state.lists[listName].page + 1);
  });
}

function changePage(listName, page) {
  state.lists[listName].page = Math.max(page, 1);
  render();
}

function bindListControls() {
  [
    ["products", elements.productsSearch, elements.productsPageSize],
    ["inventory", elements.inventorySearch, elements.inventoryPageSize],
    ["inboundDocuments", elements.inboundDocumentsSearch, elements.inboundDocumentsPageSize],
    ["outboundDocuments", elements.outboundDocumentsSearch, elements.outboundDocumentsPageSize]
  ].forEach(([listName, searchInput, pageSizeSelect]) => {
    const syncSearch = () => {
      state.lists[listName].search = searchInput.value;
      state.lists[listName].page = 1;
      render();
    };

    searchInput.addEventListener("input", syncSearch);
    searchInput.addEventListener("search", syncSearch);
    searchInput.addEventListener("change", syncSearch);

    pageSizeSelect.addEventListener("change", () => {
      state.lists[listName].pageSize = Number(pageSizeSelect.value);
      state.lists[listName].page = 1;
      render();
    });
  });
}

function openProductModal(product = null) {
  state.editingProductSkuId = product ? product.skuId : null;
  elements.productForm.reset();
  elements.productNameInput.value = product ? product.name : "";
  document.querySelector("#productModalTitle").textContent = product ? "编辑产品" : "创建产品";
  elements.submitProductButton.textContent = product ? "保存" : "创建";
  elements.productModal.hidden = false;
  elements.productNameInput.focus();
}

function closeProductModal() {
  elements.productModal.hidden = true;
  state.editingProductSkuId = null;
}

async function saveProduct(event) {
  event.preventDefault();
  const name = elements.productNameInput.value.trim();
  if (!name) {
    setMessage("请输入产品名称");
    elements.productNameInput.focus();
    return;
  }

  elements.submitProductButton.disabled = true;
  try {
    const isEditing = Boolean(state.editingProductSkuId);
    const result = await request(isEditing ? `/products/${encodeURIComponent(state.editingProductSkuId)}` : "/products", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify({ name })
    });
    Object.assign(state, result.dashboard);
    closeProductModal();
    render();
    setMessage(isEditing ? "产品已更新" : "产品已创建");
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.submitProductButton.disabled = false;
  }
}

async function deleteProduct(skuId) {
  const product = state.products.find((item) => item.skuId === skuId);
  if (!product || !window.confirm(`确认删除产品「${product.name}」？关联单件标签也会移除。`)) {
    return;
  }

  try {
    const result = await request(`/products/${encodeURIComponent(skuId)}`, { method: "DELETE" });
    Object.assign(state, result.dashboard);
    render();
    setMessage("产品已删除");
  } catch (error) {
    setMessage(error.message);
  }
}

async function deleteLabel(labelCode) {
  if (!window.confirm(`确认删除单件标签「${labelCode}」？在库标签删除后会同步扣减库存数量。`)) {
    return;
  }

  try {
    const result = await request(`/inventory/labels/${encodeURIComponent(labelCode)}`, { method: "DELETE" });
    Object.assign(state, result.dashboard);
    render();
    setMessage("标签已删除，库存已同步");
  } catch (error) {
    setMessage(error.message);
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || data.detail || "请求失败");
  }

  return data;
}

function setMessage(message) {
  elements.messageText.textContent = message;
}

function createQrImageUrl(value) {
  const encoded = encodeURIComponent(value);
  return `https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=10&data=${encoded}`;
}

function formatTime(value) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}

const routeToView = {
  "/": "inventoryView",
  "/products": "productsView",
  "/inventory": "inventoryView",
  "/inbound-documents": "inboundDocumentsView",
  "/outbound-documents": "outboundDocumentsView"
};

const viewToRoute = {
  productsView: "/products",
  inventoryView: "/inventory",
  inboundDocumentsView: "/inbound-documents",
  outboundDocumentsView: "/outbound-documents"
};

function switchView(targetViewId, options = {}) {
  document.querySelectorAll(".tab-button").forEach((item) => {
    item.classList.toggle("active", item.dataset.viewTarget === targetViewId);
  });

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === targetViewId);
  });

  const nextRoute = viewToRoute[targetViewId] || "/inventory";
  if (options.updateHistory !== false && window.location.pathname !== nextRoute) {
    window.history.pushState({ viewId: targetViewId }, "", nextRoute);
  }
}

document.querySelectorAll("[data-view-target]").forEach((button) => {
  button.addEventListener("click", () => {
    switchView(button.dataset.viewTarget);
  });
});

elements.refreshButton.addEventListener("click", () => {
  fetchDashboard().then(() => setMessage("已刷新")).catch((error) => setMessage(error.message));
});

elements.openProductModalButton.addEventListener("click", () => openProductModal());
elements.closeProductModalButton.addEventListener("click", closeProductModal);
elements.cancelProductButton.addEventListener("click", closeProductModal);
elements.productForm.addEventListener("submit", saveProduct);
elements.productList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-product-action]");
  if (!button) {
    return;
  }

  const product = state.products.find((item) => item.skuId === button.dataset.skuId);
  if (button.dataset.productAction === "edit" && product) {
    openProductModal(product);
  }
  if (button.dataset.productAction === "delete") {
    deleteProduct(button.dataset.skuId);
  }
});
elements.inventoryList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-label-action='delete']");
  if (button) {
    deleteLabel(button.dataset.labelCode);
  }
});
elements.productModal.addEventListener("click", (event) => {
  if (event.target === elements.productModal) {
    closeProductModal();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !elements.productModal.hidden) {
    closeProductModal();
  }
});

window.addEventListener("popstate", () => {
  switchView(routeToView[window.location.pathname] || "inventoryView", { updateHistory: false });
});

bindListControls();
switchView(routeToView[window.location.pathname] || "inventoryView", { updateHistory: false });

fetchDashboard().catch((error) => {
  setMessage(`后端未连接：${error.message}`);
});
