const API_BASE = window.APP_CONFIG.apiBaseUrl;

const state = {
  products: [],
  inventoryLabels: [],
  inboundDocuments: [],
  outboundDocuments: [],
  editingProductSkuId: null,
  inventoryDraftRows: [],
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
  inventoryModal: document.querySelector("#inventoryModal"),
  openInventoryModalButton: document.querySelector("#openInventoryModalButton"),
  closeInventoryModalButton: document.querySelector("#closeInventoryModalButton"),
  cancelInventoryButton: document.querySelector("#cancelInventoryButton"),
  inventoryForm: document.querySelector("#inventoryForm"),
  inventoryBatchRows: document.querySelector("#inventoryBatchRows"),
  addInventoryRowButton: document.querySelector("#addInventoryRowButton"),
  submitInventoryButton: document.querySelector("#submitInventoryButton"),
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
            <div class="product-title-row">
              <h3>${product.name}</h3>
              <button class="ghost-button" type="button" data-print-action="product" data-sku-id="${product.skuId}">全部打印</button>
            </div>
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
      <div class="label-actions">
        <button class="ghost-button label-print-button" type="button" data-print-action="label" data-label-code="${label.labelCode}">打印</button>
        <button class="danger-button label-delete-button" type="button" data-label-action="delete" data-label-code="${label.labelCode}">删除</button>
      </div>
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

function openInventoryModal() {
  state.inventoryDraftRows = [createInventoryDraftRow()];
  renderInventoryDraftRows();
  elements.inventoryModal.hidden = false;
}

function closeInventoryModal() {
  elements.inventoryModal.hidden = true;
  state.inventoryDraftRows = [];
}

function createInventoryDraftRow() {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    skuId: state.products[0]?.skuId || "",
    qualifiedQuantity: 10,
    operator: "小梅雨"
  };
}

function renderInventoryDraftRows() {
  elements.inventoryBatchRows.innerHTML = state.inventoryDraftRows.map((row, index) => `
    <fieldset class="inventory-batch-row" data-inventory-row-id="${row.id}">
      <legend>库存 ${index + 1}</legend>
      <label>
        <span>选择产品</span>
        <select data-inventory-field="skuId" required>
          ${state.products.map((product) => `
            <option value="${product.skuId}" ${product.skuId === row.skuId ? "selected" : ""}>${product.name} · ${product.skuId}</option>
          `).join("")}
        </select>
      </label>
      <label>
        <span>合格数量</span>
        <input data-inventory-field="qualifiedQuantity" type="number" min="1" step="1" value="${row.qualifiedQuantity}" required>
      </label>
      <label>
        <span>入库人</span>
        <select data-inventory-field="operator">
          ${["小梅雨", "六一"].map((operator) => `
            <option value="${operator}" ${operator === row.operator ? "selected" : ""}>${operator}</option>
          `).join("")}
        </select>
      </label>
      <button class="danger-button inventory-row-remove" type="button" data-inventory-row-remove="${row.id}" ${state.inventoryDraftRows.length <= 1 ? "disabled" : ""}>删除</button>
    </fieldset>
  `).join("");
}

function updateInventoryDraftRow(rowId, field, value) {
  const row = state.inventoryDraftRows.find((item) => item.id === rowId);
  if (!row) {
    return;
  }
  row[field] = field === "qualifiedQuantity" ? Number(value) : value;
}

function addInventoryDraftRow() {
  state.inventoryDraftRows.push(createInventoryDraftRow());
  renderInventoryDraftRows();
}

function removeInventoryDraftRow(rowId) {
  if (state.inventoryDraftRows.length <= 1) {
    return;
  }
  state.inventoryDraftRows = state.inventoryDraftRows.filter((row) => row.id !== rowId);
  renderInventoryDraftRows();
}

async function saveInventoryBatch(event) {
  event.preventDefault();
  if (state.products.length === 0) {
    setMessage("请先创建产品");
    return;
  }

  const rows = state.inventoryDraftRows.map((row) => ({
    ...row,
    product: state.products.find((product) => product.skuId === row.skuId),
    qualifiedQuantity: Number(row.qualifiedQuantity)
  }));
  const invalidRow = rows.find((row) => !row.product || !Number.isInteger(row.qualifiedQuantity) || row.qualifiedQuantity <= 0);
  if (invalidRow) {
    setMessage("请检查产品和合格数量");
    return;
  }

  elements.submitInventoryButton.disabled = true;
  try {
    let totalLabels = 0;
    for (const row of rows) {
      const inspectResult = await request("/inventory/inspect", {
        method: "POST",
        body: JSON.stringify({
          productName: row.product.name,
          qualifiedQuantity: row.qualifiedQuantity,
          inspector: row.operator
        })
      });
      const receiptId = inspectResult.receipt.receiptId;
      const inboundResult = await request("/inventory/labels/inbound", {
        method: "POST",
        body: JSON.stringify({
          receiptId,
          productMode: "existing",
          productName: row.product.name,
          operator: row.operator,
          skuId: row.skuId
        })
      });
      totalLabels += inboundResult.labels?.length || 0;
      if (inboundResult.dashboard) {
        Object.assign(state, inboundResult.dashboard);
      }
    }

    closeInventoryModal();
    await fetchDashboard();
    setMessage(`库存已创建，共新增 ${totalLabels} 个单件标签`);
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.submitInventoryButton.disabled = false;
  }
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

function printProductLabels(skuId) {
  const product = state.products.find((item) => item.skuId === skuId);
  const labels = state.inventoryLabels.filter((label) => label.skuId === skuId);
  if (!product || labels.length === 0) {
    setMessage("暂无可打印标签");
    return;
  }
  openPrintWindow(`${product.name} 单件标签`, labels);
}

function printSingleLabel(labelCode) {
  const label = state.inventoryLabels.find((item) => item.labelCode === labelCode);
  if (!label) {
    setMessage("标签不存在");
    return;
  }
  openPrintWindow(`${label.productName} ${label.labelCode}`, [label]);
}

function openPrintWindow(title, labels) {
  const printWindow = window.open("", "_blank", "width=920,height=720");
  if (!printWindow) {
    setMessage("浏览器拦截了打印窗口");
    return;
  }

  const safeTitle = escapeHtml(title);
  printWindow.document.write(`
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <title>${safeTitle}</title>
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 18px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif; color: #17202a; }
        h1 { margin: 0 0 16px; font-size: 20px; }
        .label-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
        .label-card { border: 1px solid #dfe5ec; border-radius: 8px; padding: 12px; text-align: center; break-inside: avoid; }
        .label-card img { width: 132px; height: 132px; }
        .label-card strong, .label-card span { display: block; overflow-wrap: anywhere; }
        .label-card strong { margin-top: 8px; font-size: 13px; }
        .label-card span { margin-top: 5px; color: #657282; font-size: 12px; }
        @media print { body { padding: 0; } button { display: none; } }
      </style>
    </head>
    <body>
      <h1>${safeTitle}</h1>
      <div class="label-grid">
        ${labels.map((label) => `
          <article class="label-card">
            <img src="${createQrImageUrl(label.labelCode)}" alt="${label.labelCode} 二维码">
            <strong>${escapeHtml(label.labelCode)}</strong>
            <span>${escapeHtml(label.productName)}</span>
          </article>
        `).join("")}
      </div>
      <script>
        window.addEventListener("load", () => {
          window.print();
        });
      </script>
    </body>
    </html>
  `);
  printWindow.document.close();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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
elements.openInventoryModalButton.addEventListener("click", openInventoryModal);
elements.closeInventoryModalButton.addEventListener("click", closeInventoryModal);
elements.cancelInventoryButton.addEventListener("click", closeInventoryModal);
elements.addInventoryRowButton.addEventListener("click", addInventoryDraftRow);
elements.inventoryForm.addEventListener("submit", saveInventoryBatch);
elements.inventoryBatchRows.addEventListener("input", (event) => {
  const field = event.target.dataset.inventoryField;
  const row = event.target.closest("[data-inventory-row-id]");
  if (field && row) {
    updateInventoryDraftRow(row.dataset.inventoryRowId, field, event.target.value);
  }
});
elements.inventoryBatchRows.addEventListener("change", (event) => {
  const field = event.target.dataset.inventoryField;
  const row = event.target.closest("[data-inventory-row-id]");
  if (field && row) {
    updateInventoryDraftRow(row.dataset.inventoryRowId, field, event.target.value);
  }
});
elements.inventoryBatchRows.addEventListener("click", (event) => {
  const button = event.target.closest("[data-inventory-row-remove]");
  if (button) {
    removeInventoryDraftRow(button.dataset.inventoryRowRemove);
  }
});
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
  const deleteButton = event.target.closest("[data-label-action='delete']");
  if (deleteButton) {
    deleteLabel(deleteButton.dataset.labelCode);
    return;
  }

  const printButton = event.target.closest("[data-print-action]");
  if (!printButton) {
    return;
  }
  if (printButton.dataset.printAction === "label") {
    printSingleLabel(printButton.dataset.labelCode);
  }
  if (printButton.dataset.printAction === "product") {
    printProductLabels(printButton.dataset.skuId);
  }
});
elements.productModal.addEventListener("click", (event) => {
  if (event.target === elements.productModal) {
    closeProductModal();
  }
});
elements.inventoryModal.addEventListener("click", (event) => {
  if (event.target === elements.inventoryModal) {
    closeInventoryModal();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !elements.productModal.hidden) {
    closeProductModal();
  }
  if (event.key === "Escape" && !elements.inventoryModal.hidden) {
    closeInventoryModal();
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
