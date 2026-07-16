const API_BASE = window.APP_CONFIG.apiBaseUrl;

const state = {
  products: [],
  personnel: [],
  inventoryLabels: [],
  inboundDocuments: [],
  outboundDocuments: [],
  backupStatus: null,
  editingProductSkuId: null,
  inventoryDraftRows: [],
  inventoryQualityFilter: "all",
  printTemplate: {
    templates: [],
    editorTemplateId: "default",
    editorName: "",
    status: null,
    draft: null,
    selectedElement: "qrcode",
    drag: null,
    selectedTemplateId: "default",
    pendingPrintJob: null,
    preview: {
      labelCode: "0132-010",
      productName: "懂茶帝冷萃乌龙"
    }
  },
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
  personnelForm: document.querySelector("#personnelForm"),
  personnelNameInput: document.querySelector("#personnelNameInput"),
  personnelList: document.querySelector("#personnelList"),
  submitPersonnelButton: document.querySelector("#submitPersonnelButton"),
  printTemplateForm: document.querySelector("#printTemplateForm"),
  printTemplateSelect: document.querySelector("#printTemplateSelect"),
  printTemplateName: document.querySelector("#printTemplateName"),
  newPrintTemplateButton: document.querySelector("#newPrintTemplateButton"),
  deletePrintTemplateButton: document.querySelector("#deletePrintTemplateButton"),
  printTemplateStatus: document.querySelector("#printTemplateStatus"),
  printTemplateMeta: document.querySelector("#printTemplateMeta"),
  printTemplatePreview: document.querySelector("#printTemplatePreview"),
  templateElementProperties: document.querySelector("#templateElementProperties"),
  templateSelectedElementName: document.querySelector("#templateSelectedElementName"),
  printTemplatePreviewCode: document.querySelector("#printTemplatePreviewCode"),
  printTemplatePreviewName: document.querySelector("#printTemplatePreviewName"),
  resetPrintTemplateButton: document.querySelector("#resetPrintTemplateButton"),
  savePrintTemplateButton: document.querySelector("#savePrintTemplateButton"),
  printTemplateSaveStatus: document.querySelector("#printTemplateSaveStatus"),
  printTemplatePickerModal: document.querySelector("#printTemplatePickerModal"),
  printTemplatePickerList: document.querySelector("#printTemplatePickerList"),
  printTemplatePickerHint: document.querySelector("#printTemplatePickerHint"),
  closePrintTemplatePickerButton: document.querySelector("#closePrintTemplatePickerButton"),
  cancelPrintTemplatePickerButton: document.querySelector("#cancelPrintTemplatePickerButton"),
  confirmPrintTemplatePickerButton: document.querySelector("#confirmPrintTemplatePickerButton"),
  messageText: document.querySelector("#messageText"),
  backupStatusText: document.querySelector("#backupStatusText"),
  backupButton: document.querySelector("#backupButton"),
  refreshButton: document.querySelector("#refreshButton")
};

const PRINT_TEMPLATE_FIELDS = [
  "widthMm",
  "heightMm",
  "dotsPerMm",
  "printSpeed",
  "printDensity",
  "barcodeX",
  "barcodeY",
  "barcodeWidth",
  "barcodeHeight",
  "barcodeRotation",
  "qrModules",
  "qrX",
  "qrY",
  "qrDensityMil",
  "qrCellWidth",
  "qrMode",
  "qrEncoding",
  "qrEccLevel",
  "qrQuietZoneModules",
  "qrRotation",
  "codeX",
  "codeY",
  "codeScaleX",
  "codeScaleY",
  "codeRotation",
  "textX",
  "textY",
  "textScaleX",
  "textScaleY",
  "textRotation",
  "showBarcode",
  "showQrCode",
  "showLabelCode",
  "showProductName"
];

const PRINT_TEMPLATE_BOOLEAN_FIELDS = [
  "showBarcode",
  "showQrCode",
  "showLabelCode",
  "showProductName"
];

const PRINT_TEMPLATE_FIELD_LABELS = {
  name: "模版名称",
  widthMm: "宽度 mm",
  heightMm: "高度 mm",
  dotsPerMm: "点/mm",
  printSpeed: "打印速度",
  printDensity: "打印浓度",
  barcodeX: "兼容二维码 X",
  barcodeY: "兼容二维码 Y",
  barcodeWidth: "兼容二维码宽度",
  barcodeHeight: "兼容二维码高度",
  barcodeRotation: "兼容二维码旋转",
  qrModules: "二维码模块数",
  qrX: "二维码 X",
  qrY: "二维码 Y",
  qrDensityMil: "二维码密度 mil",
  qrCellWidth: "二维码大小",
  qrMode: "二维码编码模式",
  qrEncoding: "二维码字符编码",
  qrEccLevel: "二维码纠错等级",
  qrQuietZoneModules: "二维码静区",
  qrRotation: "二维码旋转",
  codeX: "编码文字 X",
  codeY: "编码文字 Y",
  codeScaleX: "编码文字横向缩放",
  codeScaleY: "编码文字纵向缩放",
  codeRotation: "编码文字旋转",
  textX: "产品名称 X",
  textY: "产品名称 Y",
  textScaleX: "产品名称横向缩放",
  textScaleY: "产品名称纵向缩放",
  textRotation: "产品名称旋转",
  showBarcode: "兼容二维码显示",
  showQrCode: "二维码显示",
  showLabelCode: "编码文字显示",
  showProductName: "产品名称显示"
};

const PREVIEW_PIXELS_PER_MM = 8;
const DEFAULT_TEMPLATE_ID = "default";
const NEW_TEMPLATE_ID = "__new__";
const DESIGNER_PIXELS_PER_MM = 16;
const MIL_PER_MM = 39.37007874015748;
const QR_ECC_LEVEL_OPTIONS = [
  { value: 1, label: "L" },
  { value: 2, label: "M" },
  { value: 3, label: "Q" },
  { value: 4, label: "H" }
];
const QR_MODE_OPTIONS = [
  { value: 0, label: "A 自动" },
  { value: 1, label: "M 手动" }
];
const QR_ENCODING_OPTIONS = [
  { value: "ansi", label: "ANSI" },
  { value: "utf-8", label: "UTF-8" }
];
const PRINT_TEMPLATE_STRING_FIELDS = ["qrEncoding"];

const PRINT_TEMPLATE_POSITION_DOT_FIELDS = [
  "barcodeX",
  "barcodeY",
  "qrX",
  "qrY",
  "codeX",
  "codeY",
  "textX",
  "textY"
];

const PRINT_TEMPLATE_SIZE_DOT_FIELDS = [
  "barcodeWidth",
  "barcodeHeight"
];
const TEMPLATE_ELEMENTS = {
  labelCode: {
    label: "编码文字",
    showField: "showLabelCode",
    xField: "codeX",
    yField: "codeY",
    scaleXField: "codeScaleX",
    scaleYField: "codeScaleY",
    rotationField: "codeRotation"
  },
  productName: {
    label: "产品名称",
    showField: "showProductName",
    xField: "textX",
    yField: "textY",
    scaleXField: "textScaleX",
    scaleYField: "textScaleY",
    rotationField: "textRotation"
  },
  barcode: {
    label: "二维码",
    showField: "showBarcode",
    xField: "barcodeX",
    yField: "barcodeY",
    widthField: "barcodeWidth",
    heightField: "barcodeHeight",
    rotationField: "barcodeRotation"
  },
  qrcode: {
    label: "二维码",
    showField: "showQrCode",
    xField: "qrX",
    yField: "qrY",
    modulesField: "qrModules",
    cellWidthField: "qrCellWidth",
    rotationField: "qrRotation"
  }
};

async function fetchDashboard() {
  const dashboard = await request("/dashboard");
  Object.assign(state, dashboard);
  render();
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function fetchDashboardWithRetry(attempts = 2) {
  let lastError;
  for (let index = 0; index < attempts; index += 1) {
    try {
      await fetchDashboard();
      return;
    } catch (error) {
      lastError = error;
      if (index < attempts - 1) {
        await delay(350);
      }
    }
  }
  throw lastError;
}

async function fetchBackupStatus() {
  state.backupStatus = await request("/backups/status");
  renderBackupStatus();
}

async function legacyFetchPrintTemplate() {
  const template = await request("/printing/template");
  state.printTemplate.current = template.current;
  state.printTemplate.defaults = template.defaults;
  state.printTemplate.saved = template.saved;
  state.printTemplate.status = template.status;
  state.printTemplate.draft = { ...(template.current || template.defaults || {}) };
  renderPrintTemplate();
}

function render() {
  renderProducts();
  renderPersonnel();
  renderInventorySystem();
  renderInventory();
  renderDocuments();
  renderPrintTemplate();
  renderBackupStatus();
}

function getPersonnelOptions() {
  const personnel = Array.isArray(state.personnel) ? state.personnel : [];
  return personnel.length > 0
    ? personnel
    : [{ id: "person-default", name: "小梅雨" }, { id: "person-default-2", name: "六一" }];
}

function renderBackupStatus() {
  const status = state.backupStatus;
  if (!status) {
    elements.backupStatusText.textContent = "备份状态加载中";
    return;
  }

  const latestBackup = status.latestBackup;
  elements.backupStatusText.textContent = latestBackup
    ? `最近备份：${formatTime(latestBackup.createdAt)}`
    : "暂无备份";
}

function legacyRenderPrintTemplate() {
  if (!elements.printTemplateForm) {
    return;
  }

  const layout = getCurrentPrintLayout();
  syncPrintTemplateForm(layout);
  renderPrintTemplateStatus();
  renderPrintTemplateMeta(layout);
  renderPrintTemplatePreview(layout);
}

function legacySyncPrintTemplateForm(layout) {
  PRINT_TEMPLATE_FIELDS.forEach((field) => {
    const input = elements.printTemplateForm.querySelector(`[name="${field}"]`);
    if (!input) {
      return;
    }
    if (input.type === "checkbox") {
      input.checked = Boolean(layout[field]);
      return;
    }
    const nextValue = String(layout[field] ?? "");
    if (input.value !== nextValue) {
      input.value = nextValue;
    }
  });

  if (elements.printTemplatePreviewCode && elements.printTemplatePreviewCode.value !== state.printTemplate.preview.labelCode) {
    elements.printTemplatePreviewCode.value = state.printTemplate.preview.labelCode;
  }
  if (elements.printTemplatePreviewName && elements.printTemplatePreviewName.value !== state.printTemplate.preview.productName) {
    elements.printTemplatePreviewName.value = state.printTemplate.preview.productName;
  }
}

function legacyRenderPrintTemplateStatus() {
  if (!elements.printTemplateStatus) {
    return;
  }

  const status = state.printTemplate.status;
  if (!status) {
    elements.printTemplateStatus.textContent = "打印配置加载中";
    return;
  }

  const availability = status.available ? "SDK 已就绪" : (status.reason || "打印不可用");
  elements.printTemplateStatus.textContent = `${availability} | ${status.architecture} | VID ${status.vidHex || status.vid} / PID ${status.pidHex || status.pid}`;
}

function legacyRenderPrintTemplateMeta(layout) {
  if (!elements.printTemplateMeta) {
    return;
  }

  const source = state.printTemplate.saved && Object.keys(state.printTemplate.saved).length > 0
    ? "已保存自定义模版"
    : "使用默认模版";

  elements.printTemplateMeta.innerHTML = `
    <article>
      <span>模版来源</span>
      <strong>${source}</strong>
    </article>
    <article>
      <span>标签尺寸</span>
      <strong>${layout.widthMm} x ${layout.heightMm} mm</strong>
    </article>
    <article>
      <span>二维码</span>
      <strong>${layout.qrCellWidth}px cell / Y ${layout.qrY}</strong>
    </article>
    <article>
      <span>文字布局</span>
      <strong>编码 Y ${layout.codeY} / 品名 Y ${layout.textY}</strong>
    </article>
  `;
}

function legacyRenderPrintTemplatePreview(layout) {
  if (!elements.printTemplatePreview) {
    return;
  }

  const preview = state.printTemplate.preview;
  const metrics = getPreviewLabelMetrics(layout);
  elements.printTemplatePreview.innerHTML = `
    <div class="template-preview-rotated-stage" style="width:${metrics.rotatedWidthPx}px;height:${metrics.rotatedHeightPx}px;">
      <div class="template-preview-canvas template-preview-canvas-rotated" style="width:${metrics.widthPx}px;height:${metrics.heightPx}px;">
        <div class="template-preview-size">${layout.widthMm}mm x ${layout.heightMm}mm</div>
        <img
          class="template-preview-barcode"
          src="${createQrImageUrl(preview.labelCode)}"
          alt="${escapeHtml(preview.labelCode)} 二维码"
          style="left:${metrics.barcodeLeftPx}px;top:${metrics.barcodeTopPx}px;width:${metrics.barcodeWidthPx}px;height:${metrics.barcodeHeightPx}px;"
        >
        <div
          class="template-preview-code"
          style="top:${metrics.codeTopPx}px;font-size:${metrics.codeFontPx}px;transform:translateX(-50%) scaleX(${layout.codeScaleX});"
        >${escapeHtml(preview.labelCode)}</div>
        <div
          class="template-preview-name"
          style="top:${metrics.textTopPx}px;font-size:${metrics.textFontPx}px;transform:translateX(-50%) scaleX(${layout.textScaleX});"
        >${escapeHtml(preview.productName)}</div>
      </div>
    </div>
  `;
}

function legacyGetPreviewLabelMetrics(layout) {
  const dotsPerMm = Math.max(layout.dotsPerMm, 1);
  const widthPx = Math.max(layout.widthMm * PREVIEW_PIXELS_PER_MM, 160);
  const heightPx = Math.max(layout.heightMm * PREVIEW_PIXELS_PER_MM, 180);
  const qrSizePx = Math.max(((layout.qrModules * layout.qrCellWidth) / dotsPerMm) * PREVIEW_PIXELS_PER_MM, 56);

  return {
    widthPx,
    heightPx,
    rotatedWidthPx: heightPx,
    rotatedHeightPx: widthPx,
    barcodeLeftPx: (layout.barcodeX / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    barcodeTopPx: (layout.barcodeY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    barcodeWidthPx: (layout.barcodeWidth / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    barcodeHeightPx: (layout.barcodeHeight / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    qrLeftPx: (layout.qrX / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    qrTopPx: (layout.qrY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    qrSizePx,
    codeTopPx: (layout.codeY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    textTopPx: (layout.textY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    codeFontPx: Math.max(10, layout.codeScaleY * 8),
    textFontPx: Math.max(12, layout.textScaleY * 10)
  };
}

function legacyGetCurrentPrintLayout() {
  return state.printTemplate.draft
    || state.printTemplate.current
    || state.printTemplate.defaults
    || {
      widthMm: 30,
      heightMm: 40,
      dotsPerMm: 8,
      qrModules: 25,
      qrX: 45,
      qrY: 18,
      qrCellWidth: 6,
      codeY: 182,
      codeScaleX: 1,
      codeScaleY: 1,
      textY: 225,
      textScaleX: 2,
      textScaleY: 2
    };
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
    ["库存总量", engine.totalStock || 0, "all"],
    ["微瑕数量", labelStats.minorFlaw || 0, "minor_flaw"],
    ["已剪标出库", labelStats.outbound || 0, "outbound"],
    ["产品数", engine.skuCount || 0, ""]
  ];

  elements.inventoryEngineCards.innerHTML = cards.map(([label, value, filter]) => `
    <article class="${filter && state.inventoryQualityFilter === filter ? "active-filter" : ""}" ${filter ? `data-inventory-filter="${filter}"` : ""}>
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
  const qualityGradeName = label.qualityGradeName || "完品";
  return `
    <article class="label-card ${label.status} ${label.qualityGrade === "minor_flaw" ? "minor-flaw" : ""}">
      <div class="label-text">
        <strong>${label.labelCode}</strong>
        <span>${label.productName}</span>
        <span>${qualityGradeName}</span>
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
  return state.products
    .map((product) => {
      const labels = state.inventoryLabels.filter((label) => {
        if (label.skuId !== product.skuId) {
          return false;
        }
        if (state.inventoryQualityFilter === "minor_flaw") {
          return label.qualityGrade === "minor_flaw" && label.status === "in_stock";
        }
        if (state.inventoryQualityFilter === "outbound") {
          return label.status === "outbound";
        }
        return true;
      });
      return { product, labels };
    })
    .filter((item) => state.inventoryQualityFilter === "all" || item.labels.length > 0);
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

async function openInventoryModalWithRefresh() {
  elements.openInventoryModalButton.disabled = true;
  try {
    await fetchDashboardWithRetry(3);
    openInventoryModal();
  } catch (error) {
    setMessage(`刷新产品列表失败：${error.message}`);
    openInventoryModal();
  } finally {
    elements.openInventoryModalButton.disabled = false;
  }
}

function closeInventoryModal() {
  elements.inventoryModal.hidden = true;
  state.inventoryDraftRows = [];
}

function formatInventoryProductOption(product) {
  const stock = Number(product.availableStock ?? product.centralStock ?? 0);
  return `${product.name} · ${product.skuId} · ${stock}件`;
}

function getInventoryProductMatches(query) {
  const normalizedQuery = String(query || "").trim().toLocaleLowerCase();
  return state.products.filter((product) => {
    const label = formatInventoryProductOption(product).toLocaleLowerCase();
    return !normalizedQuery
      || label.includes(normalizedQuery)
      || String(product.name || "").toLocaleLowerCase().includes(normalizedQuery)
      || String(product.skuId || "").toLocaleLowerCase().includes(normalizedQuery);
  });
}

function resolveInventoryProductSelection(text) {
  const normalized = String(text || "").trim();
  if (!normalized) {
    return null;
  }
  return state.products.find((product) => {
    const label = formatInventoryProductOption(product);
    return normalized === label
      || normalized === product.name
      || normalized === product.skuId
      || normalized.startsWith(`${product.name} · `)
      || normalized.includes(` · ${product.skuId} · `);
  }) || null;
}

function createInventoryDraftRow() {
  const personnel = getPersonnelOptions();
  const product = state.products[0] || null;
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    skuId: product?.skuId || "",
    productQuery: product ? formatInventoryProductOption(product) : "",
    qualifiedQuantity: 10,
    qualityGrade: "perfect",
    operator: personnel[0]?.name || ""
  };
}

function renderInventoryDraftRows() {
  const personnel = getPersonnelOptions();
  elements.inventoryBatchRows.innerHTML = state.inventoryDraftRows.map((row, index) => `
    <fieldset class="inventory-batch-row" data-inventory-row-id="${row.id}">
      <legend>库存 ${index + 1}</legend>
      <label>
        <span>选择产品</span>
        <input
          data-inventory-field="productQuery"
          type="search"
          list="inventoryProductOptions-${escapeHtml(row.id)}"
          value="${escapeHtml(row.productQuery || "")}"
          autocomplete="off"
          required
          placeholder="输入名称或 SKU 搜索"
        >
        <datalist id="inventoryProductOptions-${escapeHtml(row.id)}">
          ${state.products.map((product) => `
            <option value="${escapeHtml(formatInventoryProductOption(product))}"></option>
          `).join("")}
        </datalist>
        <small>输入产品名称或 SKU 可模糊搜索，点击候选项选择</small>
      </label>
      <label>
        <span>合格数量</span>
        <input data-inventory-field="qualifiedQuantity" type="number" min="1" step="1" value="${row.qualifiedQuantity}" required>
      </label>
      <label>
        <span>品相</span>
        <select data-inventory-field="qualityGrade">
          <option value="perfect" ${row.qualityGrade === "perfect" ? "selected" : ""}>完品</option>
          <option value="minor_flaw" ${row.qualityGrade === "minor_flaw" ? "selected" : ""}>微瑕</option>
        </select>
      </label>
      <label>
        <span>入库人</span>
        <select data-inventory-field="operator">
          ${personnel.map((person) => `
            <option value="${escapeHtml(person.name)}" ${person.name === row.operator ? "selected" : ""}>${escapeHtml(person.name)}</option>
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
  if (field === "productQuery") {
    const product = resolveInventoryProductSelection(value);
    row.productQuery = value;
    row.skuId = product?.skuId || "";
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

  const rows = state.inventoryDraftRows.map((row) => {
    let product = state.products.find((item) => item.skuId === row.skuId) || resolveInventoryProductSelection(row.productQuery);
    if (!product) {
      const matches = getInventoryProductMatches(row.productQuery);
      product = matches.length === 1 ? matches[0] : null;
    }
    if (product) {
      row.skuId = product.skuId;
      row.productQuery = formatInventoryProductOption(product);
    }
    return {
      ...row,
      product,
      qualifiedQuantity: Number(row.qualifiedQuantity)
    };
  });
  const missingProductRow = rows.find((row) => !row.product);
  if (missingProductRow) {
    setMessage("请搜索并选择一个产品");
    return;
  }
  const invalidRow = rows.find((row) => !Number.isInteger(row.qualifiedQuantity) || row.qualifiedQuantity <= 0);
  if (invalidRow) {
    setMessage("请检查合格数量");
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
          qualityGrade: row.qualityGrade || "perfect",
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
  const isEditing = Boolean(state.editingProductSkuId);
  const editingSkuId = state.editingProductSkuId;
  try {
    const result = await request(isEditing ? `/products/${encodeURIComponent(state.editingProductSkuId)}` : "/products", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify({ name })
    });
    if (result.dashboard) {
      Object.assign(state, result.dashboard);
    }
    if (!isEditing) {
      state.lists.products.search = "";
      state.lists.products.page = 1;
      elements.productsSearch.value = "";
    }
    closeProductModal();
    render();
    setMessage(isEditing ? "产品已更新" : "产品已创建");
  } catch (error) {
    const recovered = await recoverProductSaveAfterNetworkError({ name, isEditing, editingSkuId, error });
    if (recovered) {
      return;
    }
    setMessage(error.message);
  } finally {
    elements.submitProductButton.disabled = false;
  }
}

async function recoverProductSaveAfterNetworkError({ name, isEditing, editingSkuId, error }) {
  if (!/Failed to fetch|NetworkError|Load failed/i.test(error.message || "")) {
    return false;
  }

  try {
    await fetchDashboardWithRetry(3);
    const saved = isEditing
      ? state.products.some((product) => product.skuId === editingSkuId && product.name === name)
      : state.products.some((product) => product.name === name);
    if (!saved) {
      return false;
    }
    closeProductModal();
    setMessage(isEditing ? "产品已更新，列表已刷新" : "产品已创建，列表已刷新");
    return true;
  } catch {
    return false;
  }
}

async function deleteProduct(skuId) {
  const product = state.products.find((item) => item.skuId === skuId);
  if (!product || !window.confirm(`确认删除产品「${product.name}」？关联单件标签也会移除。`)) {
    return;
  }

  try {
    const result = await request(`/products/${encodeURIComponent(skuId)}`, { method: "DELETE" });
    if (result.dashboard) {
      Object.assign(state, result.dashboard);
    } else {
      state.products = state.products.filter((item) => item.skuId !== skuId);
    }
    render();
    setMessage("产品已删除");
  } catch (error) {
    const recovered = await recoverProductDeleteAfterNetworkError({ skuId, error });
    if (recovered) {
      return;
    }
    setMessage(error.message);
  }
}

async function recoverProductDeleteAfterNetworkError({ skuId, error }) {
  if (!/Failed to fetch|NetworkError|Load failed/i.test(error.message || "")) {
    return false;
  }

  try {
    await fetchDashboardWithRetry(3);
    const deleted = !state.products.some((product) => product.skuId === skuId);
    if (!deleted) {
      return false;
    }
    setMessage("产品已删除，列表已刷新");
    return true;
  } catch {
    return false;
  }
}

async function savePersonnel(event) {
  event.preventDefault();
  const name = elements.personnelNameInput.value.trim();
  if (!name) {
    setMessage("请输入人员姓名");
    elements.personnelNameInput.focus();
    return;
  }

  elements.submitPersonnelButton.disabled = true;
  try {
    const result = await request("/personnel", {
      method: "POST",
      body: JSON.stringify({ name })
    });
    if (result.dashboard) {
      Object.assign(state, result.dashboard);
    } else {
      state.personnel = result.personnel || state.personnel;
    }
    elements.personnelNameInput.value = "";
    render();
    setMessage(`已添加人员：${result.person?.name || name}`);
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.submitPersonnelButton.disabled = false;
  }
}

async function deletePersonnel(personId) {
  try {
    const result = await request(`/personnel/${encodeURIComponent(personId)}`, {
      method: "DELETE"
    });
    if (result.dashboard) {
      Object.assign(state, result.dashboard);
    } else {
      state.personnel = result.personnel || state.personnel;
    }
    const firstPerson = getPersonnelOptions()[0]?.name || "";
    state.inventoryDraftRows.forEach((row) => {
      if (!getPersonnelOptions().some((person) => person.name === row.operator)) {
        row.operator = firstPerson;
      }
    });
    render();
    setMessage(`已删除人员：${result.person?.name || ""}`);
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

async function createManualBackup() {
  elements.backupButton.disabled = true;
  setMessage("正在备份数据库");
  try {
    const result = await request("/backups", { method: "POST" });
    state.backupStatus = result.status;
    renderBackupStatus();
    setMessage(`备份完成：${result.backup.filename}`);
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.backupButton.disabled = false;
  }
}

function legacyUpdatePrintTemplateDraft(field, value) {
  const nextValue = Number(value);
  if (!Number.isFinite(nextValue)) {
    return;
  }
  state.printTemplate.draft = {
    ...getCurrentPrintLayout(),
    [field]: nextValue
  };
  renderPrintTemplate();
}

function renderPersonnel() {
  if (!elements.personnelList) {
    return;
  }
  const personnel = getPersonnelOptions();
  elements.personnelList.innerHTML = personnel.length > 0
    ? personnel.map((person) => `
      <article class="personnel-card">
        <div>
          <strong>${escapeHtml(person.name)}</strong>
          <span>${escapeHtml(person.id)}</span>
        </div>
        <button class="danger-button" type="button" data-personnel-delete="${escapeHtml(person.id)}" ${personnel.length <= 1 ? "disabled" : ""}>删除</button>
      </article>
    `).join("")
    : `<div class="empty-state">暂无人员</div>`;
}

async function legacySavePrintTemplate(event) {
  event.preventDefault();
  const payload = { ...getCurrentPrintLayout() };
  elements.savePrintTemplateButton.disabled = true;
  try {
    const template = await request("/printing/template", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    state.printTemplate.current = template.current;
    state.printTemplate.defaults = template.defaults;
    state.printTemplate.saved = template.saved;
    state.printTemplate.status = template.status;
    state.printTemplate.draft = { ...(template.current || {}) };
    renderPrintTemplate();
    setMessage("打印模版已保存");
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.savePrintTemplateButton.disabled = false;
  }
}

async function legacyResetPrintTemplate() {
  elements.resetPrintTemplateButton.disabled = true;
  try {
    const template = await request("/printing/template", {
      method: "DELETE"
    });
    state.printTemplate.current = template.current;
    state.printTemplate.defaults = template.defaults;
    state.printTemplate.saved = template.saved;
    state.printTemplate.status = template.status;
    state.printTemplate.draft = { ...(template.current || template.defaults || {}) };
    renderPrintTemplate();
    setMessage("已恢复默认打印模版");
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.resetPrintTemplateButton.disabled = false;
  }
}

async function legacyPrintProductLabels(skuId) {
  const product = state.products.find((item) => item.skuId === skuId);
  const labels = state.inventoryLabels.filter((label) => label.skuId === skuId);
  if (!product || labels.length === 0) {
    setMessage("暂无可打印标签");
    return;
  }
  await sendLabelsToPrinter({
    title: `${product.name} 单件标签`,
    labels,
    path: `/printing/products/${encodeURIComponent(skuId)}`
  });
}

async function legacyPrintSingleLabel(labelCode) {
  const label = state.inventoryLabels.find((item) => item.labelCode === labelCode);
  if (!label) {
    setMessage("标签不存在");
    return;
  }
  await sendLabelsToPrinter({
    title: `${label.productName} ${label.labelCode}`,
    labels: [label],
    path: `/printing/labels/${encodeURIComponent(labelCode)}`
  });
}

async function legacySendLabelsToPrinter({ title, labels, path }) {
  try {
    const result = await request(path, { method: "POST" });
    setMessage(`打印任务已发送，共 ${result.printed} 个标签`);
  } catch (error) {
    setMessage(`打印服务未连接，已打开预览：${error.message}`);
    openPrintWindow(title, labels);
  }
}

function legacyOpenPrintWindow(title, labels) {
  const printWindow = window.open("", "_blank", "width=920,height=720");
  if (!printWindow) {
    setMessage("浏览器拦截了打印窗口");
    return;
  }

  const layout = getCurrentPrintLayout();
  const qrSizeMm = Math.max((layout.qrModules * layout.qrCellWidth) / Math.max(layout.dotsPerMm, 1), 12);
  const safeTitle = escapeHtml(title);
  printWindow.document.write(`
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <title>${safeTitle}</title>
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 18px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif; color: #111; }
        h1 { margin: 0 0 16px; font-size: 20px; }
        .label-grid { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-start; }
        .label-card { width: ${layout.widthMm}mm; height: ${layout.heightMm}mm; border: 1px solid #dfe5ec; border-radius: 2mm; padding: 2mm; text-align: center; break-inside: avoid; page-break-inside: avoid; }
        .label-card img { display: block; width: ${qrSizeMm}mm; height: ${qrSizeMm}mm; margin: 2mm auto 1.5mm; image-rendering: pixelated; }
        .label-card strong { display: block; color: #111; font-size: 7pt; font-weight: 700; line-height: 1.15; letter-spacing: 0; overflow-wrap: anywhere; }
        .label-card span { display: block; margin-top: 1mm; color: #111; font-size: 11pt; font-weight: 600; line-height: 1.15; overflow-wrap: anywhere; }
        @page { size: ${layout.widthMm}mm ${layout.heightMm}mm; margin: 0; }
        @media print {
          body { padding: 0; }
          h1 { display: none; }
          .label-grid { display: block; }
          .label-card { border: 0; page-break-after: always; }
        }
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
    throw new Error(formatRequestError(data));
  }

  return data;
}

function formatRequestError(data) {
  if (data?.message) {
    return data.message;
  }
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => {
      const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : "";
      const label = PRINT_TEMPLATE_FIELD_LABELS[field] || field || "字段";
      return `${label}: ${item.msg || "校验失败"}`;
    }).join("；");
  }
  if (typeof data?.detail === "string") {
    return data.detail;
  }
  return "请求失败";
}

function setMessage(message) {
  elements.messageText.textContent = message;
}

function setPrintTemplateSaveStatus(message, stateName = "idle") {
  if (!elements.printTemplateSaveStatus) {
    return;
  }
  elements.printTemplateSaveStatus.textContent = message;
  elements.printTemplateSaveStatus.dataset.state = stateName;
}

function markPrintTemplateDirty(message = "有未保存修改") {
  setPrintTemplateSaveStatus(message, "dirty");
}

function formatCurrentClockTime() {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(new Date());
}

function createQrImageUrl(value) {
  const encoded = encodeURIComponent(value);
  return `https://api.qrserver.com/v1/create-qr-code/?size=160x160&margin=8&data=${encoded}`;
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

function buildDefaultPrintLayout() {
  return {
    widthMm: 30,
    heightMm: 40,
    dotsPerMm: 8,
    printSpeed: 8,
    printDensity: 4,
    barcodeX: 45,
    barcodeY: 18,
    barcodeWidth: 150,
    barcodeHeight: 67,
    barcodeRotation: 0,
    qrModules: 25,
    qrX: 45,
    qrY: 18,
    qrDensityMil: 24.63,
    qrCellWidth: 5,
    qrMode: 0,
    qrEncoding: "ansi",
    qrEccLevel: 2,
    qrQuietZoneModules: 4,
    qrRotation: 0,
    codeX: -1,
    codeY: 182,
    codeScaleX: 1,
    codeScaleY: 1,
    codeRotation: 0,
    textX: -1,
    textY: 225,
    textScaleX: 2,
    textScaleY: 2,
    textRotation: 0,
    showBarcode: false,
    showQrCode: true,
    showLabelCode: true,
    showProductName: true
  };
}

function buildDefaultClientTemplate() {
  return {
    id: DEFAULT_TEMPLATE_ID,
    name: "默认模版",
    isDefault: true,
    layout: buildDefaultPrintLayout()
  };
}

function normalizePrintLayout(layout = {}) {
  const normalized = {
    ...buildDefaultPrintLayout(),
    ...layout
  };
  normalized.qrModules = Math.max(21, Number(normalized.qrModules) || 21);
  normalized.qrDensityMil = Number(normalized.qrDensityMil) || dotsToMil(normalized.qrCellWidth, normalized);
  normalized.qrCellWidth = Math.min(Math.max(milToDots(normalized.qrDensityMil, normalized), 1), 20);
  normalized.qrMode = Number(normalized.qrMode) === 1 ? 1 : 0;
  normalized.qrEncoding = normalized.qrEncoding === "utf-8" ? "utf-8" : "ansi";
  normalized.qrEccLevel = Math.min(Math.max(Number(normalized.qrEccLevel) || 2, 1), 4);
  normalized.qrQuietZoneModules = Math.min(Math.max(Number(normalized.qrQuietZoneModules) || 4, 0), 8);
  normalized.printDensity = Math.min(Math.max(Number(normalized.printDensity) || 4, 1), 15);
  normalized.printSpeed = Math.min(Math.max(Number(normalized.printSpeed) || 8, 1), 10);
  normalized.qrX = Math.max(Number(normalized.qrX) || 0, 0);
  normalized.qrY = Math.max(Number(normalized.qrY) || 0, 0);
  return normalized;
}

function dotsToMm(value, layout) {
  return Number(value || 0) / Math.max(Number(layout.dotsPerMm) || 1, 1);
}

function dotsToMil(value, layout) {
  return dotsToMm(value, layout) * MIL_PER_MM;
}

function mmToDots(value, layout) {
  return Math.max(0, Math.round(Number(value || 0) * Math.max(Number(layout.dotsPerMm) || 1, 1)));
}

function milToDots(value, layout) {
  const dotsPerMm = Math.max(Number(layout.dotsPerMm) || 1, 1);
  return Math.max(1, Math.round((Number(value || 0) / MIL_PER_MM) * dotsPerMm));
}

function formatMm(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0";
  }
  return String(Math.round(number * 100) / 100);
}

function formatMil(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0";
  }
  return String(Math.round(number * 100) / 100);
}

function getElementPositionMm(layout, elementId) {
  const element = TEMPLATE_ELEMENTS[elementId];
  return {
    x: dotsToMm(resolveElementXDots(layout, elementId), layout),
    y: dotsToMm(layout[element.yField], layout)
  };
}

function getTextWidthDots(value, scale = 1) {
  return Array.from(String(value || "")).reduce((width, char) => width + (char.charCodeAt(0) > 127 ? 16 : 8), 0) * Math.max(Number(scale) || 1, 1);
}

function resolveElementXDots(layout, elementId) {
  const element = TEMPLATE_ELEMENTS[elementId];
  if (elementId === "labelCode") {
    return resolvePrintTextXDots(layout, state.printTemplate.preview.labelCode, element.xField, element.scaleXField);
  }
  if (elementId === "productName") {
    return resolvePrintTextXDots(layout, state.printTemplate.preview.productName, element.xField, element.scaleXField);
  }
  const rawX = Number(layout[element.xField]);
  if (Number.isFinite(rawX) && rawX >= 0) {
    return rawX;
  }
  return 0;
}

function resolvePrintTextXDots(layout, value, xField, scaleField) {
  const rawX = Number(layout[xField]);
  if (Number.isFinite(rawX) && rawX >= 0) {
    return rawX;
  }
  return Math.max((intLabelWidthDots(layout) - getTextWidthDots(value, layout[scaleField])) / 2, 0);
}

function resolveElementPositionDots(layout, elementId) {
  const element = TEMPLATE_ELEMENTS[elementId];
  return {
    x: Math.round(resolveElementXDots(layout, elementId)),
    y: Math.max(0, Number(layout[element.yField]) || 0)
  };
}

function intLabelWidthDots(layout) {
  return intMmToDots(layout.widthMm, layout);
}

function intMmToDots(valueMm, layout) {
  return Math.round(Number(valueMm || 0) * Math.max(Number(layout.dotsPerMm) || 1, 1));
}

function getPrintTemplateById(templateId) {
  return state.printTemplate.templates.find((template) => template.id === templateId) || null;
}

function resolvePrintTemplateId(templateId) {
  if (templateId === NEW_TEMPLATE_ID) {
    return NEW_TEMPLATE_ID;
  }
  if (templateId && getPrintTemplateById(templateId)) {
    return templateId;
  }
  return state.printTemplate.templates[0]?.id || DEFAULT_TEMPLATE_ID;
}

function getCurrentPrintLayout() {
  return state.printTemplate.draft || { ...buildDefaultPrintLayout() };
}

function getCurrentEditorTemplate() {
  if (state.printTemplate.editorTemplateId === NEW_TEMPLATE_ID) {
    return {
      id: NEW_TEMPLATE_ID,
      name: state.printTemplate.editorName || "新模版",
      isDefault: false,
      layout: getCurrentPrintLayout()
    };
  }
  return getPrintTemplateById(state.printTemplate.editorTemplateId) || buildDefaultClientTemplate();
}

function applyPrintTemplateState(data, preferredTemplateId = null, preferredLayout = null) {
  const incomingTemplates = Array.isArray(data.templates) && data.templates.length > 0
    ? data.templates
    : [buildDefaultClientTemplate()];
  state.printTemplate.templates = incomingTemplates.map((template) => ({
    ...template,
    layout: normalizePrintLayout(template.layout)
  }));
  state.printTemplate.status = data.status || null;

  const nextEditorId = resolvePrintTemplateId(preferredTemplateId || data.editorTemplateId || state.printTemplate.editorTemplateId);
  if (nextEditorId === NEW_TEMPLATE_ID) {
    startNewPrintTemplate(false);
  } else {
    const editorTemplate = getPrintTemplateById(nextEditorId) || state.printTemplate.templates[0];
    state.printTemplate.editorTemplateId = editorTemplate.id;
    state.printTemplate.editorName = editorTemplate.name;
    state.printTemplate.draft = normalizePrintLayout(preferredLayout || editorTemplate.layout);
  }

  if (nextEditorId !== NEW_TEMPLATE_ID && getPrintTemplateById(nextEditorId)) {
    state.printTemplate.selectedTemplateId = nextEditorId;
  } else if (!getPrintTemplateById(state.printTemplate.selectedTemplateId)) {
    state.printTemplate.selectedTemplateId = state.printTemplate.templates[0]?.id || DEFAULT_TEMPLATE_ID;
  }

  renderPrintTemplate();
  setPrintTemplateSaveStatus("已加载", "saved");
}

async function fetchPrintTemplate() {
  applyPrintTemplateState(await request("/printing/template"));
}

function startNewPrintTemplate(shouldRender = true, shouldMarkDirty = true) {
  state.printTemplate.editorTemplateId = NEW_TEMPLATE_ID;
  state.printTemplate.editorName = "新模版";
  state.printTemplate.draft = normalizePrintLayout(getCurrentPrintLayout());
  if (shouldRender) {
    renderPrintTemplate();
  }
  if (shouldMarkDirty) {
    markPrintTemplateDirty("新模版未保存");
  }
}

function renderPrintTemplate() {
  if (!elements.printTemplateForm) {
    return;
  }

  const layout = getCurrentPrintLayout();
  syncPrintTemplateForm(layout);
  renderPrintTemplateStatus();
  renderPrintTemplateMeta(layout);
  renderPrintTemplatePreview(layout);
  renderPrintTemplatePicker();
}

function syncPrintTemplateForm(layout) {
  PRINT_TEMPLATE_FIELDS.forEach((field) => {
    const input = elements.printTemplateForm.querySelector(`[name="${field}"]`);
    if (!input) {
      return;
    }
    if (input.type === "checkbox") {
      input.checked = Boolean(layout[field]);
      return;
    }
    const nextValue = String(layout[field] ?? "");
    if (input.value !== nextValue) {
      input.value = nextValue;
    }
  });

  if (elements.printTemplateSelect) {
    elements.printTemplateSelect.innerHTML = `
      ${state.printTemplate.templates.map((template) => `
        <option value="${template.id}" ${template.id === state.printTemplate.editorTemplateId ? "selected" : ""}>
          ${escapeHtml(template.name)}${template.isDefault ? "（默认）" : ""}
        </option>
      `).join("")}
      <option value="${NEW_TEMPLATE_ID}" ${state.printTemplate.editorTemplateId === NEW_TEMPLATE_ID ? "selected" : ""}>新建模版</option>
    `;
  }

  if (elements.printTemplateName && elements.printTemplateName.value !== state.printTemplate.editorName) {
    elements.printTemplateName.value = state.printTemplate.editorName;
  }

  const editorTemplate = getCurrentEditorTemplate();
  if (elements.deletePrintTemplateButton) {
    elements.deletePrintTemplateButton.disabled = editorTemplate.isDefault || editorTemplate.id === NEW_TEMPLATE_ID;
  }
  if (elements.savePrintTemplateButton) {
    elements.savePrintTemplateButton.textContent = editorTemplate.id === NEW_TEMPLATE_ID || editorTemplate.isDefault
      ? "保存为新模版"
      : "保存修改";
  }

  if (elements.printTemplatePreviewCode && elements.printTemplatePreviewCode.value !== state.printTemplate.preview.labelCode) {
    elements.printTemplatePreviewCode.value = state.printTemplate.preview.labelCode;
  }
  if (elements.printTemplatePreviewName && elements.printTemplatePreviewName.value !== state.printTemplate.preview.productName) {
    elements.printTemplatePreviewName.value = state.printTemplate.preview.productName;
  }
}

function renderPrintTemplateStatus() {
  if (!elements.printTemplateStatus) {
    return;
  }

  const status = state.printTemplate.status;
  if (!status) {
    elements.printTemplateStatus.textContent = "打印配置加载中";
    return;
  }

  const availability = status.available ? "SDK 已就绪" : (status.reason || "打印不可用");
  elements.printTemplateStatus.textContent = `${availability} | ${status.architecture} | VID ${status.vidHex || status.vid} / PID ${status.pidHex || status.pid}`;
}

function renderPrintTemplateMeta(layout) {
  if (!elements.printTemplateMeta) {
    return;
  }

  const enabledElements = Object.entries(TEMPLATE_ELEMENTS)
    .filter(([, element]) => layout[element.showField])
    .map(([, element]) => element.label)
    .join(" / ") || "未选择元素";

  elements.printTemplateMeta.innerHTML = `
    <article>
      <span>标签</span>
      <strong>${formatMm(layout.widthMm)} x ${formatMm(layout.heightMm)} mm</strong>
    </article>
    <article>
      <span>精度</span>
      <strong>${layout.dotsPerMm} dots/mm · 最小 ${formatMm(1 / Math.max(layout.dotsPerMm, 1))} mm</strong>
    </article>
    <article>
      <span>元素</span>
      <strong>${enabledElements}</strong>
    </article>
    <article>
      <span>方向</span>
      <strong>元素独立旋转</strong>
    </article>
  `;
}

function renderPrintTemplatePreview(layout) {
  if (!elements.printTemplatePreview) {
    return;
  }

  const preview = state.printTemplate.preview;
  const canvasWidthPx = Math.max(layout.widthMm * DESIGNER_PIXELS_PER_MM, 1);
  const canvasHeightPx = Math.max(layout.heightMm * DESIGNER_PIXELS_PER_MM, 1);
  const barcodeWidthPx = dotsToMm(layout.barcodeWidth, layout) * DESIGNER_PIXELS_PER_MM;
  const barcodeHeightPx = dotsToMm(layout.barcodeHeight, layout) * DESIGNER_PIXELS_PER_MM;
  const qrSizePx = dotsToMm(layout.qrModules * layout.qrCellWidth, layout) * DESIGNER_PIXELS_PER_MM;
  const codeX = dotsToMm(resolveElementXDots(layout, "labelCode"), layout);
  const textX = dotsToMm(resolveElementXDots(layout, "productName"), layout);

  const items = [
    layout.showLabelCode ? `
      <div class="designer-element designer-text ${state.printTemplate.selectedElement === "labelCode" ? "is-selected" : ""}"
        data-template-element="labelCode"
        style="left:${codeX * DESIGNER_PIXELS_PER_MM}px;top:${dotsToMm(layout.codeY, layout) * DESIGNER_PIXELS_PER_MM}px;font-size:${Math.max(12, layout.codeScaleY * 12)}px;transform:rotate(${layout.codeRotation || 0}deg) scaleX(${layout.codeScaleX});transform-origin:left top;">
        ${escapeHtml(preview.labelCode)}
      </div>
    ` : "",
    layout.showProductName ? `
      <div class="designer-element designer-text designer-product-name ${state.printTemplate.selectedElement === "productName" ? "is-selected" : ""}"
        data-template-element="productName"
        style="left:${textX * DESIGNER_PIXELS_PER_MM}px;top:${dotsToMm(layout.textY, layout) * DESIGNER_PIXELS_PER_MM}px;font-size:${Math.max(16, layout.textScaleY * 14)}px;transform:rotate(${layout.textRotation || 0}deg) scaleX(${layout.textScaleX});transform-origin:left top;">
        ${escapeHtml(preview.productName)}
      </div>
    ` : "",
    layout.showBarcode ? `
      <img class="designer-element designer-barcode ${state.printTemplate.selectedElement === "barcode" ? "is-selected" : ""}"
        data-template-element="barcode"
        src="${createQrImageUrl(preview.labelCode)}"
        alt="${escapeHtml(preview.labelCode)} 二维码"
        style="left:${dotsToMm(layout.barcodeX, layout) * DESIGNER_PIXELS_PER_MM}px;top:${dotsToMm(layout.barcodeY, layout) * DESIGNER_PIXELS_PER_MM}px;width:${barcodeWidthPx}px;height:${barcodeHeightPx}px;transform:rotate(${layout.barcodeRotation || 0}deg);transform-origin:left top;">
    ` : "",
    layout.showQrCode ? `
      <img class="designer-element designer-qrcode ${state.printTemplate.selectedElement === "qrcode" ? "is-selected" : ""}"
        data-template-element="qrcode"
        src="${createQrImageUrl(preview.labelCode)}"
        alt="${escapeHtml(preview.labelCode)} 二维码"
        style="left:${dotsToMm(layout.qrX, layout) * DESIGNER_PIXELS_PER_MM}px;top:${dotsToMm(layout.qrY, layout) * DESIGNER_PIXELS_PER_MM}px;width:${qrSizePx}px;height:${qrSizePx}px;transform:rotate(${layout.qrRotation || 0}deg);transform-origin:left top;">
    ` : ""
  ].join("");

  elements.printTemplatePreview.innerHTML = `
    <div class="designer-canvas-viewport" style="width:${canvasWidthPx}px;height:${canvasHeightPx}px;" data-template-canvas="true">
      <div class="designer-print-direction-badge">自定义模板预览</div>
      <div class="designer-canvas" style="width:${canvasWidthPx}px;height:${canvasHeightPx}px;">
        <div class="designer-canvas-size">${formatMm(layout.widthMm)}mm x ${formatMm(layout.heightMm)}mm</div>
        ${items}
      </div>
    </div>
  `;

  renderTemplateElementProperties(layout);
}

function renderTemplateElementProperties(layout) {
  if (!elements.templateElementProperties || !elements.templateSelectedElementName) {
    return;
  }

  const selectedId = state.printTemplate.selectedElement;
  const element = TEMPLATE_ELEMENTS[selectedId] || TEMPLATE_ELEMENTS.qrcode;
  state.printTemplate.selectedElement = selectedId in TEMPLATE_ELEMENTS ? selectedId : "qrcode";
  elements.templateSelectedElementName.textContent = element.label;
  const enabled = Boolean(layout[element.showField]);
  const xMm = element.xField ? dotsToMm(layout[element.xField], layout) : 0;
  const yMm = element.yField ? dotsToMm(layout[element.yField], layout) : 0;
  const qrDensityMil = formatMil(layout.qrDensityMil || dotsToMil(layout.qrCellWidth, layout));
  const recommendedQrDots = milToDots(24.63, layout);
  const qrEccOptions = QR_ECC_LEVEL_OPTIONS.map((option) => `
    <option value="${option.value}" ${Number(layout.qrEccLevel) === option.value ? "selected" : ""}>${option.label}</option>
  `).join("");
  const qrModeOptions = QR_MODE_OPTIONS.map((option) => `
    <option value="${option.value}" ${Number(layout.qrMode) === option.value ? "selected" : ""}>${option.label}</option>
  `).join("");
  const qrEncodingOptions = QR_ENCODING_OPTIONS.map((option) => `
    <option value="${option.value}" ${layout.qrEncoding === option.value ? "selected" : ""}>${option.label}</option>
  `).join("");

  const positionFields = `
    <label class="template-toggle property-toggle"><input name="${element.showField}" type="checkbox" ${enabled ? "checked" : ""}><span>启用${element.label}</span></label>
    <label><span>X mm</span><input data-template-mm-field="${element.xField}" type="number" min="0" step="0.1" value="${formatMm(xMm)}"></label>
    <label><span>Y mm</span><input data-template-mm-field="${element.yField}" type="number" min="0" step="0.1" value="${formatMm(yMm)}"></label>
    <label><span>旋转 °</span><input name="${element.rotationField}" type="number" min="-3600" max="3600" step="1" value="${layout[element.rotationField] || 0}"></label>
  `;

  let extraFields = "";
  if (selectedId === "barcode") {
    extraFields = `
      <label><span>宽度 mm</span><input data-template-mm-field="barcodeWidth" type="number" min="1" step="0.1" value="${formatMm(dotsToMm(layout.barcodeWidth, layout))}"></label>
      <label><span>高度 mm</span><input data-template-mm-field="barcodeHeight" type="number" min="1" step="0.1" value="${formatMm(dotsToMm(layout.barcodeHeight, layout))}"></label>
    `;
  } else if (selectedId === "qrcode") {
    extraFields = `
      <label><span>二维码密度 mil</span><input data-template-qr-density-mil="true" type="number" min="4" max="100" step="0.01" value="${qrDensityMil}"></label>
      <label><span>SDK 单元宽 dots</span><input name="qrCellWidth" type="number" min="1" max="20" step="1" value="${layout.qrCellWidth}"></label>
      <label><span>静区模块</span><input name="qrQuietZoneModules" type="number" min="0" max="8" step="1" value="${layout.qrQuietZoneModules}"></label>
      <label><span>编码模式</span><select name="qrMode">${qrModeOptions}</select></label>
      <label><span>字符编码</span><select name="qrEncoding">${qrEncodingOptions}</select></label>
      <label><span>纠错等级</span><select name="qrEccLevel">${qrEccOptions}</select></label>
      <label><span>打印浓度</span><input name="printDensity" type="number" min="1" max="15" step="1" value="${layout.printDensity}"></label>
      <label><span>打印速度</span><input name="printSpeed" type="number" min="1" max="10" step="1" value="${layout.printSpeed}"></label>
      <div class="property-help">当前密度 ${qrDensityMil} mil，换算为 ${layout.qrCellWidth} dots；静区 ${layout.qrQuietZoneModules} 模块 = ${layout.qrQuietZoneModules * layout.qrCellWidth} dots。字符编码已支持 ANSI / UTF-8。</div>
    `;
  } else {
    extraFields = `
      <label><span>横向缩放</span><input name="${element.scaleXField}" type="number" min="1" max="8" step="1" value="${layout[element.scaleXField]}"></label>
      <label><span>纵向缩放</span><input name="${element.scaleYField}" type="number" min="1" max="8" step="1" value="${layout[element.scaleYField]}"></label>
      <button class="ghost-button property-full-button" type="button" data-template-center-text="${selectedId}">自动居中</button>
    `;
  }

  elements.templateElementProperties.innerHTML = `${positionFields}${extraFields}`;
}

function getPreviewLabelMetrics(layout) {
  const dotsPerMm = Math.max(layout.dotsPerMm, 1);
  const widthPx = Math.max(layout.widthMm * PREVIEW_PIXELS_PER_MM, 160);
  const heightPx = Math.max(layout.heightMm * PREVIEW_PIXELS_PER_MM, 180);
  const qrSizePx = Math.max(((layout.qrModules * layout.qrCellWidth) / dotsPerMm) * PREVIEW_PIXELS_PER_MM, 56);

  return {
    widthPx,
    heightPx,
    rotatedWidthPx: heightPx,
    rotatedHeightPx: widthPx,
    barcodeLeftPx: (layout.barcodeX / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    barcodeTopPx: (layout.barcodeY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    barcodeWidthPx: (layout.barcodeWidth / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    barcodeHeightPx: (layout.barcodeHeight / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    qrLeftPx: (layout.qrX / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    qrTopPx: (layout.qrY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    qrSizePx,
    codeTopPx: (layout.codeY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    textTopPx: (layout.textY / dotsPerMm) * PREVIEW_PIXELS_PER_MM,
    codeFontPx: Math.max(10, layout.codeScaleY * 8),
    textFontPx: Math.max(12, layout.textScaleY * 10)
  };
}
function renderPrintTemplatePicker() {
  if (!elements.printTemplatePickerList) {
    return;
  }

  const selectedTemplateId = resolvePrintTemplateId(state.printTemplate.selectedTemplateId);
  state.printTemplate.selectedTemplateId = selectedTemplateId;
  elements.printTemplatePickerList.innerHTML = state.printTemplate.templates.map((template) => `
    <label class="template-picker-option">
      <input type="radio" name="printTemplateChoice" value="${template.id}" ${template.id === selectedTemplateId ? "checked" : ""}>
      <span class="template-picker-option-name">${escapeHtml(template.name)}</span>
      <span class="template-picker-option-meta">${template.layout.widthMm} x ${template.layout.heightMm} mm</span>
    </label>
  `).join("");
}

function updatePrintTemplateDraft(field, value) {
  const nextValue = PRINT_TEMPLATE_BOOLEAN_FIELDS.includes(field)
    ? Boolean(value)
    : PRINT_TEMPLATE_STRING_FIELDS.includes(field)
      ? String(value)
      : Number(value);
  if (
    !PRINT_TEMPLATE_BOOLEAN_FIELDS.includes(field)
    && !PRINT_TEMPLATE_STRING_FIELDS.includes(field)
    && !Number.isFinite(nextValue)
  ) {
    return;
  }
  const currentLayout = normalizePrintLayout(getCurrentPrintLayout());
  if (field === "dotsPerMm") {
    state.printTemplate.draft = scalePrintLayoutDotsPerMm(currentLayout, nextValue);
    markPrintTemplateDirty();
    renderPrintTemplate();
    return;
  }
  state.printTemplate.draft = {
    ...currentLayout,
    [field]: nextValue
  };
  if (field === "qrCellWidth") {
    state.printTemplate.draft.qrDensityMil = Number(formatMil(dotsToMil(nextValue, state.printTemplate.draft)));
  }
  markPrintTemplateDirty();
  renderPrintTemplate();
}

function scalePrintLayoutDotsPerMm(layout, nextDotsPerMm) {
  const previousDotsPerMm = Math.max(Number(layout.dotsPerMm) || 1, 1);
  const safeNextDotsPerMm = Math.max(Number(nextDotsPerMm) || previousDotsPerMm, 1);
  const ratio = safeNextDotsPerMm / previousDotsPerMm;
  const nextLayout = {
    ...layout,
    dotsPerMm: safeNextDotsPerMm
  };

  PRINT_TEMPLATE_POSITION_DOT_FIELDS.forEach((field) => {
    nextLayout[field] = Math.max(0, Math.round((Number(layout[field]) || 0) * ratio));
  });
  PRINT_TEMPLATE_SIZE_DOT_FIELDS.forEach((field) => {
    nextLayout[field] = Math.max(1, Math.round((Number(layout[field]) || 0) * ratio));
  });
  nextLayout.qrCellWidth = Math.min(Math.max(milToDots(nextLayout.qrDensityMil, nextLayout), 1), 20);
  return nextLayout;
}

function updatePrintTemplateDraftMm(field, value) {
  const layout = normalizePrintLayout(getCurrentPrintLayout());
  state.printTemplate.draft = {
    ...layout,
    [field]: mmToDots(value, layout)
  };
  markPrintTemplateDirty();
  renderPrintTemplate();
}

function updatePrintTemplateQrDensityMil(value) {
  const layout = normalizePrintLayout(getCurrentPrintLayout());
  const qrDensityMil = Math.min(Math.max(Number(value) || 24.63, 4), 100);
  state.printTemplate.draft = {
    ...layout,
    qrDensityMil,
    qrCellWidth: Math.min(Math.max(milToDots(qrDensityMil, layout), 1), 20)
  };
  markPrintTemplateDirty();
  renderPrintTemplate();
}

function selectTemplateElement(elementId) {
  if (!(elementId in TEMPLATE_ELEMENTS)) {
    return;
  }
  const layout = normalizePrintLayout(getCurrentPrintLayout());
  const element = TEMPLATE_ELEMENTS[elementId];
  state.printTemplate.selectedElement = elementId;
  if (!layout[element.showField]) {
    state.printTemplate.draft = {
      ...layout,
      [element.showField]: true
    };
    markPrintTemplateDirty();
  }
  renderPrintTemplate();
}

function startTemplateElementDrag(event) {
  const target = event.target.closest("[data-template-element]");
  if (!target) {
    return;
  }
  const elementId = target.dataset.templateElement;
  if (!(elementId in TEMPLATE_ELEMENTS)) {
    return;
  }
  event.preventDefault();
  const layout = normalizePrintLayout(getCurrentPrintLayout());
  const element = TEMPLATE_ELEMENTS[elementId];
  const rect = elements.printTemplatePreview.querySelector("[data-template-canvas]")?.getBoundingClientRect();
  if (!rect) {
    return;
  }
  state.printTemplate.selectedElement = elementId;
  const startPosition = resolveElementPositionDots(layout, elementId);
  state.printTemplate.drag = {
    elementId,
    startClientX: event.clientX,
    startClientY: event.clientY,
    startX: startPosition.x,
    startY: startPosition.y
  };
  window.addEventListener("pointermove", moveTemplateElementDrag);
  window.addEventListener("pointerup", endTemplateElementDrag);
  renderPrintTemplate();
}

function moveTemplateElementDrag(event) {
  const drag = state.printTemplate.drag;
  if (!drag) {
    return;
  }
  const layout = normalizePrintLayout(getCurrentPrintLayout());
  const element = TEMPLATE_ELEMENTS[drag.elementId];
  const visualDeltaX = (event.clientX - drag.startClientX) / DESIGNER_PIXELS_PER_MM;
  const visualDeltaY = (event.clientY - drag.startClientY) / DESIGNER_PIXELS_PER_MM;
  const deltaX = Math.round(visualDeltaX * layout.dotsPerMm);
  const deltaY = Math.round(visualDeltaY * layout.dotsPerMm);
  state.printTemplate.draft = {
    ...layout,
    [element.xField]: Math.max(0, drag.startX + deltaX),
    [element.yField]: Math.max(0, drag.startY + deltaY)
  };
  markPrintTemplateDirty();
  renderPrintTemplate();
}

function endTemplateElementDrag() {
  state.printTemplate.drag = null;
  window.removeEventListener("pointermove", moveTemplateElementDrag);
  window.removeEventListener("pointerup", endTemplateElementDrag);
}

async function savePrintTemplate(event) {
  event.preventDefault();
  const editorTemplate = getCurrentEditorTemplate();
  const isCreatingTemplate = state.printTemplate.editorTemplateId === NEW_TEMPLATE_ID || state.printTemplate.editorTemplateId === DEFAULT_TEMPLATE_ID;
  const rawName = (elements.printTemplateName?.value || state.printTemplate.editorName || "新模版").trim() || "新模版";
  const payload = {
    name: editorTemplate.isDefault ? `${rawName}副本` : rawName,
    ...getCurrentPrintLayout()
  };

  elements.savePrintTemplateButton.disabled = true;
  setPrintTemplateSaveStatus("正在保存...", "saving");
  try {
    const response = isCreatingTemplate
      ? await request("/printing/template", {
        method: "POST",
        body: JSON.stringify(payload)
      })
      : await request(`/printing/template/${encodeURIComponent(state.printTemplate.editorTemplateId)}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });

    const savedTemplateId = response.editorTemplateId || (!isCreatingTemplate ? state.printTemplate.editorTemplateId : null);
    applyPrintTemplateState(response, savedTemplateId, payload);
    setPrintTemplateSaveStatus(
      `${isCreatingTemplate ? "已另存为新模版" : "已保存"} ${formatCurrentClockTime()}`,
      "saved"
    );
    setMessage(editorTemplate.isDefault ? "默认模版已另存为新模版" : "打印模版已保存");
  } catch (error) {
    setPrintTemplateSaveStatus(`保存失败：${error.message}`, "error");
    setMessage(error.message);
  } finally {
    elements.savePrintTemplateButton.disabled = false;
  }
}

async function resetPrintTemplate() {
  startNewPrintTemplate();
  state.printTemplate.draft = normalizePrintLayout(buildDefaultPrintLayout());
  state.printTemplate.editorName = "新模版";
  renderPrintTemplate();
  markPrintTemplateDirty("默认参数未保存");
  setMessage("已载入默认参数，可另存为新模版");
}

async function deletePrintTemplate() {
  const editorTemplate = getCurrentEditorTemplate();
  if (editorTemplate.isDefault || editorTemplate.id === NEW_TEMPLATE_ID) {
    return;
  }
  if (!window.confirm(`确认删除打印模版「${editorTemplate.name}」？`)) {
    return;
  }

  elements.deletePrintTemplateButton.disabled = true;
  try {
    const response = await request(`/printing/template/${encodeURIComponent(editorTemplate.id)}`, {
      method: "DELETE"
    });
    applyPrintTemplateState(response);
    setMessage("打印模版已删除");
  } catch (error) {
    setMessage(error.message);
  } finally {
    elements.deletePrintTemplateButton.disabled = false;
  }
}

async function printProductLabels(skuId) {
  const product = state.products.find((item) => item.skuId === skuId);
  const labels = state.inventoryLabels.filter((label) => label.skuId === skuId);
  if (!product || labels.length === 0) {
    setMessage("暂无可打印标签");
    return;
  }
  await queuePrintJob({
    title: `${product.name} 单件标签`,
    labels
  });
}

async function printSingleLabel(labelCode) {
  const label = state.inventoryLabels.find((item) => item.labelCode === labelCode);
  if (!label) {
    setMessage("标签不存在");
    return;
  }
  await queuePrintJob({
    title: `${label.productName} ${label.labelCode}`,
    labels: [label]
  });
}

async function queuePrintJob(job) {
  if (state.printTemplate.templates.length === 0) {
    await fetchPrintTemplate();
  }
  state.printTemplate.pendingPrintJob = job;
  openPrintTemplatePicker();
}

function openPrintTemplatePicker() {
  state.printTemplate.selectedTemplateId = resolvePrintTemplateId(state.printTemplate.selectedTemplateId);
  renderPrintTemplatePicker();
  if (elements.printTemplatePickerHint) {
    const count = state.printTemplate.pendingPrintJob?.labels?.length || 0;
    elements.printTemplatePickerHint.textContent = `本次将打印 ${count} 个标签，请选择模版。`;
  }
  if (elements.printTemplatePickerModal) {
    elements.printTemplatePickerModal.hidden = false;
  }
}

function closePrintTemplatePicker() {
  if (elements.printTemplatePickerModal) {
    elements.printTemplatePickerModal.hidden = true;
  }
  state.printTemplate.pendingPrintJob = null;
}

async function confirmPrintWithSelectedTemplate() {
  const job = state.printTemplate.pendingPrintJob;
  if (!job) {
    closePrintTemplatePicker();
    return;
  }

  const checked = elements.printTemplatePickerList?.querySelector("input[name='printTemplateChoice']:checked");
  const templateId = checked?.value || resolvePrintTemplateId(state.printTemplate.selectedTemplateId);
  state.printTemplate.selectedTemplateId = templateId;

  try {
    await sendLabelsToPrinter({
      title: job.title,
      labels: job.labels,
      templateId
    });
  } finally {
    closePrintTemplatePicker();
  }
}

async function sendLabelsToPrinter({ title, labels, templateId }) {
  try {
    const result = await request("/printing/labels", {
      method: "POST",
      body: JSON.stringify({
        labels: labels.map((label) => ({
          labelCode: label.labelCode,
          productName: label.productName
        })),
        copies: 1,
        templateId
      })
    });
    setMessage(`打印任务已发送，共 ${result.printed} 个标签`);
  } catch (error) {
    setMessage(`打印服务未连接，已打开预览：${error.message}`);
    openPrintWindow(title, labels, templateId);
  }
}

function openPrintWindow(title, labels, templateId = DEFAULT_TEMPLATE_ID) {
  const printWindow = window.open("", "_blank", "width=920,height=720");
  if (!printWindow) {
    setMessage("浏览器拦截了打印窗口");
    return;
  }

  const template = getPrintTemplateById(templateId) || buildDefaultClientTemplate();
  const layout = normalizePrintLayout(template.layout);
  const dotsPerMm = Math.max(layout.dotsPerMm, 1);
  const barcodeLeftMm = layout.barcodeX / dotsPerMm;
  const barcodeTopMm = layout.barcodeY / dotsPerMm;
  const barcodeWidthMm = layout.barcodeWidth / dotsPerMm;
  const barcodeHeightMm = layout.barcodeHeight / dotsPerMm;
  const qrSizeMm = Math.max((layout.qrModules * layout.qrCellWidth) / dotsPerMm, 12);
  const qrLeftMm = layout.qrX / dotsPerMm;
  const qrTopMm = layout.qrY / dotsPerMm;
  const codeTopMm = dotsToMm(layout.codeY, layout);
  const textTopMm = dotsToMm(layout.textY, layout);
  const codeFontMm = Math.max(2.2, layout.codeScaleY * 3);
  const textFontMm = Math.max(2.8, layout.textScaleY * 3.2);
  const safeTitle = escapeHtml(title);
  const buildTextStyle = ({ leftMm, topMm, scaleX, rotation, fontMm, weight }) => [
    `left:${formatMm(leftMm)}mm`,
    `top:${formatMm(topMm)}mm`,
    `font-size:${formatMm(fontMm)}mm`,
    `font-weight:${weight}`,
    `transform:rotate(${rotation || 0}deg) scaleX(${scaleX})`
  ].join(";");
  printWindow.document.write(`
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <title>${safeTitle}</title>
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 18px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif; color: #111; }
        h1 { margin: 0 0 16px; font-size: 20px; }
        .label-grid { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-start; }
        .label-card { position: relative; width: ${layout.widthMm}mm; height: ${layout.heightMm}mm; border: 1px solid #dfe5ec; border-radius: 2mm; padding: 0; text-align: center; break-inside: avoid; page-break-inside: avoid; overflow: hidden; }
        .label-art { position: absolute; top: 0; left: 0; width: ${layout.widthMm}mm; height: ${layout.heightMm}mm; }
        .label-card img { position: absolute; display: block; image-rendering: pixelated; object-fit: contain; }
        .label-barcode { left: ${barcodeLeftMm}mm; top: ${barcodeTopMm}mm; width: ${barcodeWidthMm}mm; height: ${barcodeHeightMm}mm; transform: rotate(${layout.barcodeRotation || 0}deg); transform-origin: left top; }
        .label-qrcode { left: ${qrLeftMm}mm; top: ${qrTopMm}mm; width: ${qrSizeMm}mm; height: ${qrSizeMm}mm; transform: rotate(${layout.qrRotation || 0}deg); transform-origin: left top; }
        .label-text { position: absolute; display: block; color: #111; line-height: 1; letter-spacing: 0; white-space: nowrap; transform-origin: left top; }
        @page { size: ${layout.widthMm}mm ${layout.heightMm}mm; margin: 0; }
        @media print {
          body { padding: 0; }
          h1 { display: none; }
          .label-grid { display: block; }
          .label-card { border: 0; page-break-after: always; }
        }
      </style>
    </head>
    <body>
      <h1>${safeTitle}</h1>
      <div class="label-grid">
        ${labels.map((label) => `
          <article class="label-card">
            <div class="label-art">
            ${layout.showBarcode ? `<img class="label-barcode" src="${createQrImageUrl(label.labelCode)}" alt="${escapeHtml(label.labelCode)} 二维码">` : ""}
              ${layout.showQrCode ? `<img class="label-qrcode" src="${createQrImageUrl(label.labelCode)}" alt="${escapeHtml(label.labelCode)} 二维码">` : ""}
              ${layout.showLabelCode ? `<strong class="label-text label-code" style="${buildTextStyle({
                leftMm: dotsToMm(resolvePrintTextXDots(layout, label.labelCode, "codeX", "codeScaleX"), layout),
                topMm: codeTopMm,
                scaleX: layout.codeScaleX,
                rotation: layout.codeRotation,
                fontMm: codeFontMm,
                weight: 700
              })}">${escapeHtml(label.labelCode)}</strong>` : ""}
              ${layout.showProductName ? `<span class="label-text label-name" style="${buildTextStyle({
                leftMm: dotsToMm(resolvePrintTextXDots(layout, label.productName, "textX", "textScaleX"), layout),
                topMm: textTopMm,
                scaleX: layout.textScaleX,
                rotation: layout.textRotation,
                fontMm: textFontMm,
                weight: 700
              })}">${escapeHtml(label.productName)}</span>` : ""}
            </div>
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
const routeToView = {
  "/": "inventoryView",
  "/products": "productsView",
  "/inventory": "inventoryView",
  "/inbound-documents": "inboundDocumentsView",
  "/outbound-documents": "outboundDocumentsView",
  "/personnel": "personnelView",
  "/print-template": "printTemplateView"
};

const viewToRoute = {
  productsView: "/products",
  inventoryView: "/inventory",
  inboundDocumentsView: "/inbound-documents",
  outboundDocumentsView: "/outbound-documents",
  personnelView: "/personnel",
  printTemplateView: "/print-template"
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

function refreshViewData(targetViewId) {
  if (targetViewId === "printTemplateView") {
    fetchPrintTemplate().catch((error) => setMessage(error.message));
    return;
  }
  fetchDashboard().catch((error) => setMessage(error.message));
}

document.querySelectorAll("[data-view-target]").forEach((button) => {
  button.addEventListener("click", () => {
    switchView(button.dataset.viewTarget);
    refreshViewData(button.dataset.viewTarget);
  });
});

elements.refreshButton.addEventListener("click", () => {
  Promise.all([fetchDashboard(), fetchBackupStatus(), fetchPrintTemplate()])
    .then(() => setMessage("已刷新"))
    .catch((error) => setMessage(error.message));
});
elements.backupButton.addEventListener("click", createManualBackup);

elements.openProductModalButton.addEventListener("click", () => openProductModal());
elements.closeProductModalButton.addEventListener("click", closeProductModal);
elements.cancelProductButton.addEventListener("click", closeProductModal);
elements.productForm.addEventListener("submit", saveProduct);
elements.openInventoryModalButton.addEventListener("click", openInventoryModalWithRefresh);
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
elements.inventoryEngineCards.addEventListener("click", (event) => {
  const card = event.target.closest("[data-inventory-filter]");
  if (!card) {
    return;
  }
  state.inventoryQualityFilter = card.dataset.inventoryFilter || "all";
  state.lists.inventory.page = 1;
  render();
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
elements.personnelForm?.addEventListener("submit", savePersonnel);
elements.personnelList?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-personnel-delete]");
  if (!button) {
    return;
  }
  deletePersonnel(button.dataset.personnelDelete);
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
elements.printTemplateForm?.addEventListener("input", (event) => {
  const field = event.target.name;
  if (PRINT_TEMPLATE_FIELDS.includes(field)) {
    updatePrintTemplateDraft(field, event.target.type === "checkbox" ? event.target.checked : event.target.value);
  }
});
elements.printTemplateForm?.addEventListener("submit", savePrintTemplate);
elements.printTemplatePreview?.addEventListener("pointerdown", startTemplateElementDrag);
function handleTemplateElementPropertyChange(event) {
  const field = event.target.name;
  if (event.target.dataset.templateMmField) {
    updatePrintTemplateDraftMm(event.target.dataset.templateMmField, event.target.value);
    return;
  }
  if (event.target.dataset.templateQrDensityMil) {
    updatePrintTemplateQrDensityMil(event.target.value);
    return;
  }
  if (PRINT_TEMPLATE_FIELDS.includes(field)) {
    updatePrintTemplateDraft(field, event.target.type === "checkbox" ? event.target.checked : event.target.value);
  }
}

elements.templateElementProperties?.addEventListener("input", handleTemplateElementPropertyChange);
elements.templateElementProperties?.addEventListener("change", handleTemplateElementPropertyChange);
elements.templateElementProperties?.addEventListener("click", (event) => {
  const centerButton = event.target.closest("[data-template-center-text]");
  if (!centerButton) {
    return;
  }
  const elementId = centerButton.dataset.templateCenterText;
  const element = TEMPLATE_ELEMENTS[elementId];
  if (!element) {
    return;
  }
  state.printTemplate.draft = {
    ...normalizePrintLayout(getCurrentPrintLayout()),
    [element.xField]: -1
  };
  renderPrintTemplate();
  markPrintTemplateDirty();
});
document.querySelectorAll("[data-template-select-element]").forEach((button) => {
  button.addEventListener("click", () => selectTemplateElement(button.dataset.templateSelectElement));
});
elements.resetPrintTemplateButton?.addEventListener("click", resetPrintTemplate);
elements.newPrintTemplateButton?.addEventListener("click", () => {
  startNewPrintTemplate();
});
elements.deletePrintTemplateButton?.addEventListener("click", deletePrintTemplate);
elements.printTemplateSelect?.addEventListener("change", (event) => {
  const nextId = event.target.value;
  if (nextId === NEW_TEMPLATE_ID) {
    startNewPrintTemplate();
    return;
  }
  const template = getPrintTemplateById(nextId);
  if (!template) {
    return;
  }
  state.printTemplate.editorTemplateId = template.id;
  state.printTemplate.editorName = template.name;
  state.printTemplate.draft = normalizePrintLayout(template.layout);
  renderPrintTemplate();
  setPrintTemplateSaveStatus("已加载", "saved");
});
elements.printTemplateName?.addEventListener("input", (event) => {
  state.printTemplate.editorName = event.target.value;
  markPrintTemplateDirty();
});
elements.printTemplatePreviewCode?.addEventListener("input", (event) => {
  state.printTemplate.preview.labelCode = event.target.value || "0132-010";
  renderPrintTemplate();
});
elements.printTemplatePreviewName?.addEventListener("input", (event) => {
  state.printTemplate.preview.productName = event.target.value || "懂茶帝冷萃乌龙";
  renderPrintTemplate();
});
elements.printTemplatePickerList?.addEventListener("change", (event) => {
  if (event.target.name === "printTemplateChoice") {
    state.printTemplate.selectedTemplateId = event.target.value;
  }
});
elements.closePrintTemplatePickerButton?.addEventListener("click", closePrintTemplatePicker);
elements.cancelPrintTemplatePickerButton?.addEventListener("click", closePrintTemplatePicker);
elements.confirmPrintTemplatePickerButton?.addEventListener("click", confirmPrintWithSelectedTemplate);
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
elements.printTemplatePickerModal?.addEventListener("click", (event) => {
  if (event.target === elements.printTemplatePickerModal) {
    closePrintTemplatePicker();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !elements.productModal.hidden) {
    closeProductModal();
  }
  if (event.key === "Escape" && !elements.inventoryModal.hidden) {
    closeInventoryModal();
  }
  if (event.key === "Escape" && elements.printTemplatePickerModal && !elements.printTemplatePickerModal.hidden) {
    closePrintTemplatePicker();
  }
});

window.addEventListener("popstate", () => {
  const targetViewId = routeToView[window.location.pathname] || "inventoryView";
  switchView(targetViewId, { updateHistory: false });
  refreshViewData(targetViewId);
});

bindListControls();
switchView(routeToView[window.location.pathname] || "inventoryView", { updateHistory: false });

Promise.all([fetchDashboard(), fetchBackupStatus(), fetchPrintTemplate()]).catch((error) => {
  setMessage(`后端未连接：${error.message}`);
});
