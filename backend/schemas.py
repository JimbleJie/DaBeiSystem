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


class EmptyRequest(BaseModel):
    pass
