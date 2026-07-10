from pydantic import BaseModel, Field


class SimulateOrderRequest(BaseModel):
    platformId: str
    skuId: str
    quantity: int = Field(default=1, ge=1)
    buyer: str | None = None


class PullOrdersRequest(BaseModel):
    platformId: str | None = None


class InboundStockRequest(BaseModel):
    skuId: str
    quantity: int = Field(ge=1)
    batchNo: str | None = None
    productionDate: str | None = None
    expiryDate: str | None = None
    supplier: str | None = None
    warehouse: str | None = None
    qualityResult: str | None = None
    purchaseOrderNo: str | None = None
    operator: str | None = None


class CreateProductRequest(BaseModel):
    name: str
    spec: str = "标准款"
    unit: str = "件"
    category: str = "默认分类"
    barcode: str | None = None
    skuId: str | None = None
    price: float = Field(default=0, ge=0)
    initialStock: int = Field(default=0, ge=0)
    batchNo: str | None = None
    productionDate: str | None = None
    expiryDate: str | None = None
    supplier: str | None = None
    warehouse: str = "主仓"
    safeStock: int = Field(default=5, ge=0)
    operator: str | None = None


class UpdateProductRequest(BaseModel):
    name: str


class OutboundStockRequest(BaseModel):
    skuId: str
    quantity: int = Field(ge=1)
    channelId: str
    outboundType: str = "channel_sale"
    recipient: str | None = None
    operator: str | None = None
    remark: str | None = None


class InspectReceiptRequest(BaseModel):
    productName: str = "壶"
    qualifiedQuantity: int = Field(ge=1)
    inspector: str | None = None


class LabelInboundRequest(BaseModel):
    receiptId: str
    productMode: str = "existing"
    skuId: str | None = None
    productName: str | None = None
    operator: str | None = None


class LabelOutboundRequest(BaseModel):
    labelCode: str
    reasonId: str
    operator: str | None = None
    remark: str | None = None


class PrintLabelItem(BaseModel):
    labelCode: str
    productName: str


class PrintLabelsRequest(BaseModel):
    labels: list[PrintLabelItem]
    copies: int = Field(default=1, ge=1, le=99)
    templateId: str | None = None


class PrintTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    widthMm: float = Field(ge=5, le=120)
    heightMm: float = Field(ge=5, le=120)
    dotsPerMm: int = Field(ge=4, le=24)
    printSpeed: int = Field(default=8, ge=1, le=10)
    printDensity: int = Field(default=4, ge=1, le=15)
    barcodeX: int = Field(ge=0, le=2000)
    barcodeY: int = Field(ge=0, le=2000)
    barcodeWidth: int = Field(ge=20, le=2000)
    barcodeHeight: int = Field(ge=10, le=1000)
    barcodeRotation: int = Field(default=0, ge=-3600, le=3600)
    qrModules: int = Field(ge=1, le=41)
    qrX: int = Field(ge=0, le=2000)
    qrY: int = Field(ge=0, le=2000)
    qrDensityMil: float = Field(default=24.63, ge=4, le=100)
    qrCellWidth: int = Field(ge=1, le=20)
    qrMode: int = Field(default=0, ge=0, le=1)
    qrEncoding: str = Field(default="ansi", pattern="^(ansi|utf-8)$")
    qrEccLevel: int = Field(default=2, ge=1, le=4)
    qrQuietZoneModules: int = Field(default=4, ge=0, le=8)
    qrRotation: int = Field(default=0, ge=-3600, le=3600)
    codeX: int = Field(ge=-1, le=2000)
    codeY: int = Field(ge=0, le=2000)
    codeScaleX: int = Field(ge=1, le=6)
    codeScaleY: int = Field(ge=1, le=6)
    codeRotation: int = Field(default=0, ge=-3600, le=3600)
    textX: int = Field(ge=-1, le=2000)
    textY: int = Field(ge=0, le=2000)
    textScaleX: int = Field(ge=1, le=8)
    textScaleY: int = Field(ge=1, le=8)
    textRotation: int = Field(default=0, ge=-3600, le=3600)
    showBarcode: bool = False
    showQrCode: bool = True
    showLabelCode: bool = True
    showProductName: bool = True


class EmptyRequest(BaseModel):
    pass
