package com.dabeisys.inventory;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Filter;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;

import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final int GREEN = Color.rgb(31, 118, 102);
    private static final int TEXT = Color.rgb(23, 32, 42);
    private static final int MUTED = Color.rgb(101, 114, 130);
    private static final int BG = Color.rgb(244, 246, 248);
    private static final String PAGE_HOME = "home";
    private static final String PAGE_SETTINGS = "settings";
    private static final String PAGE_INBOUND = "inbound";
    private static final String PAGE_OUTBOUND = "outbound";

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final List<ProductOption> products = new ArrayList<>();
    private final List<LabelOption> labels = new ArrayList<>();
    private final List<ReasonOption> reasons = new ArrayList<>();
    private final List<String> personnel = new ArrayList<>();
    private final List<String> pageStack = new ArrayList<>();
    private JSONObject dashboard;
    private EditText outboundLabelInput;
    private String currentPage = PAGE_HOME;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        showHome();
        refreshDashboard(true);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }

    @Override
    public void onBackPressed() {
        if (navigateBack()) {
            return;
        }
        super.onBackPressed();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, android.content.Intent data) {
        IntentResult result = IntentIntegrator.parseActivityResult(requestCode, resultCode, data);
        if (result != null) {
            if (result.getContents() == null) {
                toast("已取消扫码");
                return;
            }
            if (outboundLabelInput != null) {
                outboundLabelInput.setText(result.getContents().trim());
            }
            toast("扫码成功");
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    private void showHome() {
        currentPage = PAGE_HOME;
        outboundLabelInput = null;
        pageStack.clear();
        LinearLayout page = pageRoot();
        page.addView(title("大北库存", "连接后台后执行入库、出库和库存展示"));

        Button settingsButton = secondaryButton("设置");
        settingsButton.setOnClickListener(view -> navigateTo(PAGE_SETTINGS));
        page.addView(settingsButton);

        Button refreshButton = secondaryButton("刷新后台数据");
        refreshButton.setOnClickListener(view -> refreshDashboard(true, true));
        page.addView(refreshButton);

        Button inboundButton = primaryButton("入库");
        inboundButton.setOnClickListener(view -> navigateTo(PAGE_INBOUND));
        page.addView(inboundButton);

        Button outboundButton = primaryButton("出库");
        outboundButton.setOnClickListener(view -> navigateTo(PAGE_OUTBOUND));
        page.addView(outboundButton);

        page.addView(sectionTitle("库存展示"));
        page.addView(bodyText(summaryText()));
        setContentView(wrap(page));
    }

    private void refreshDashboard() {
        refreshDashboard(false);
    }

    private void showSettings() {
        currentPage = PAGE_SETTINGS;
        outboundLabelInput = null;
        LinearLayout page = pageRoot();
        page.addView(title("设置", "配置后台 IP、端口和 API 路径"));
        page.addView(backButton());

        EditText hostInput = input("后台 IP，例如 192.168.1.10");
        hostInput.setText(prefs().getString("host", "10.0.2.2"));
        page.addView(label("后台 IP"));
        page.addView(hostInput);

        EditText portInput = input("端口，例如 4000");
        portInput.setInputType(InputType.TYPE_CLASS_NUMBER);
        portInput.setText(String.valueOf(prefs().getInt("port", 4000)));
        page.addView(label("端口"));
        page.addView(portInput);

        EditText pathInput = input("API 路径，例如 /api");
        pathInput.setText(prefs().getString("apiPath", "/api"));
        page.addView(label("API 路径"));
        page.addView(pathInput);
        page.addView(sectionTitle("当前后台地址"));
        page.addView(bodyText(apiBase()));

        Button saveButton = primaryButton("保存并测试连接");
        saveButton.setOnClickListener(view -> {
            String host = hostInput.getText().toString().trim();
            int port = parseInt(portInput.getText().toString());
            String apiPath = pathInput.getText().toString().trim();
            if (host.isEmpty() || port <= 0 || apiPath.isEmpty()) {
                toast("请填写完整配置");
                return;
            }
            prefs().edit()
                    .putString("host", host)
                    .putInt("port", port)
                    .putString("apiPath", apiPath.startsWith("/") ? apiPath : "/" + apiPath)
                    .apply();
            request("GET", "/health", null, json -> {
                toast("连接成功");
                showSettings();
                refreshDashboard(false);
            }, error -> toast("连接失败：" + error));
        });
        page.addView(saveButton);
        setContentView(wrap(page));
    }

    private void showInbound() {
        currentPage = PAGE_INBOUND;
        outboundLabelInput = null;
        LinearLayout page = pageRoot();
        page.addView(title("入库", "选择后台已有产品，录入合格数量后创建二维码并入库"));
        page.addView(backButton());

        page.addView(label("选择产品"));
        AutoCompleteTextView productInput = productSearchInput();
        final ProductOption[] selectedProduct = {null};
        productInput.setOnItemClickListener((parent, view, position, id) -> {
            String selectedText = view instanceof TextView ? ((TextView) view).getText().toString() : "";
            if (selectedText.trim().isEmpty() && position >= 0 && position < parent.getAdapter().getCount()) {
                Object item = parent.getAdapter().getItem(position);
                selectedText = item == null ? "" : item.toString();
            }
            selectedProduct[0] = resolveProductSelection(selectedText);
            if (selectedProduct[0] != null) {
                productInput.setText(formatProductOption(selectedProduct[0]), false);
            }
        });
        productInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence text, int start, int count, int after) {
            }

            @Override
            public void onTextChanged(CharSequence text, int start, int before, int count) {
            }

            @Override
            public void afterTextChanged(Editable editable) {
                selectedProduct[0] = resolveProductSelection(editable.toString());
            }
        });
        page.addView(productInput);
        page.addView(hintText("输入产品名称或 SKU 可模糊搜索；如果没有查到产品，请到后台添加"));

        page.addView(label("合格数量："));
        EditText qualifiedInput = input("例如 10");
        qualifiedInput.setInputType(InputType.TYPE_CLASS_NUMBER);
        qualifiedInput.setText("10");
        page.addView(qualifiedInput);

        Spinner operatorSpinner = spinner(personnelNames());
        page.addView(label("选择入库人"));
        page.addView(operatorSpinner);

        TextView result = bodyText("");
        Button createButton = primaryButton("创建并入库");
        createButton.setOnClickListener(view -> {
            if (products.isEmpty()) {
                toast("没有查到产品，请到后台添加");
                return;
            }

            ProductOption product = selectedProduct[0];
            if (product == null) {
                List<String> matches = productSearchLabels(productInput.getText().toString());
                if (matches.size() == 1) {
                    product = resolveProductSelection(matches.get(0));
                }
            }
            if (product == null) {
                toast("请搜索并选择一个产品");
                productInput.requestFocus();
                productInput.showDropDown();
                return;
            }

            String productName = product.name;
            String skuId = product.skuId;
            int qualified = parseInt(qualifiedInput.getText().toString());
            String operator = operatorSpinner.getSelectedItem().toString();

            if (qualified <= 0) {
                toast("请填写合格数量");
                return;
            }

            try {
                JSONObject inspectBody = new JSONObject()
                        .put("productName", productName)
                        .put("qualifiedQuantity", qualified)
                        .put("inspector", operator);
                request("POST", "/inventory/inspect", inspectBody, inspectJson -> {
                    String receiptId = inspectJson.optJSONObject("receipt").optString("receiptId");
                    try {
                        JSONObject inboundBody = new JSONObject()
                                .put("receiptId", receiptId)
                                .put("productMode", "existing")
                                .put("productName", productName)
                                .put("operator", operator)
                                .put("skuId", skuId);
                        request("POST", "/inventory/labels/inbound", inboundBody, inboundJson -> {
                            JSONArray qrCodes = inboundJson.optJSONArray("labels");
                            int count = qrCodes == null ? 0 : qrCodes.length();
                            result.setText(formatInboundResult(inboundJson, count));
                            toast("入库成功，已创建 " + count + " 个二维码");
                            refreshDashboard(false);
                        }, error -> toast("入库失败：" + error));
                    } catch (Exception error) {
                        toast("入库参数错误：" + error.getMessage());
                    }
                }, error -> toast("核检失败：" + error));
            } catch (Exception error) {
                toast("请求参数错误：" + error.getMessage());
            }
        });
        page.addView(createButton);
        page.addView(sectionTitle("入库结果"));
        page.addView(result);
        setContentView(wrap(page));
    }

    private void showOutbound() {
        currentPage = PAGE_OUTBOUND;
        LinearLayout page = pageRoot();
        page.addView(title("出库", "扫描二维码后出库，后台扣减库存并标记剪标"));
        page.addView(backButton());

        outboundLabelInput = input("点击扫码出库后自动填入二维码标签");
        outboundLabelInput.setFocusable(false);
        outboundLabelInput.setFocusableInTouchMode(false);
        page.addView(label("扫码标签"));
        page.addView(outboundLabelInput);

        Button scanButton = secondaryButton("扫码出库");
        scanButton.setOnClickListener(view -> startQrScan());
        page.addView(scanButton);

        Spinner reasonSpinner = spinner(reasonNames());
        page.addView(label("出库原因"));
        page.addView(reasonSpinner);

        Spinner operatorSpinner = spinner(personnelNames());
        page.addView(label("出库人"));
        page.addView(operatorSpinner);

        EditText remarkInput = input("备注，例如 装盒前已复核并剪标");
        page.addView(label("备注"));
        page.addView(remarkInput);

        TextView result = bodyText("");
        Button outboundButton = primaryButton("确认出库");
        outboundButton.setOnClickListener(view -> {
            String labelCode = outboundLabelInput.getText().toString().trim();
            ReasonOption reason = reasons.get(reasonSpinner.getSelectedItemPosition());
            if (labelCode.isEmpty()) {
                toast("请先扫码");
                return;
            }
            try {
                JSONObject body = new JSONObject()
                        .put("labelCode", labelCode)
                        .put("reasonId", reason.id)
                        .put("operator", operatorSpinner.getSelectedItem().toString())
                        .put("remark", remarkInput.getText().toString().trim());
                request("POST", "/inventory/labels/outbound", body, json -> {
                    result.setText(formatOutboundResult(json));
                    toast("出库成功，库存已同步");
                    refreshDashboard(false);
                }, error -> handleOutboundError(error));
            } catch (Exception error) {
                toast("请求参数错误：" + error.getMessage());
            }
        });
        page.addView(outboundButton);
        page.addView(sectionTitle("出库结果"));
        page.addView(result);
        setContentView(wrap(page));
    }

    private void startQrScan() {
        IntentIntegrator integrator = new IntentIntegrator(this);
        integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE);
        integrator.setPrompt("扫描出库二维码");
        integrator.setBeepEnabled(true);
        integrator.setOrientationLocked(true);
        integrator.initiateScan();
    }

    private void navigateTo(String page) {
        if (!currentPage.equals(page)) {
            pageStack.add(currentPage);
        }
        if (shouldRefreshBeforeRender(page)) {
            refreshAndRenderPage(page);
            return;
        }
        renderPage(page);
    }

    private boolean navigateBack() {
        if (pageStack.isEmpty()) {
            return false;
        }
        String previousPage = pageStack.remove(pageStack.size() - 1);
        renderPage(previousPage);
        return true;
    }

    private void renderPage(String page) {
        if (PAGE_SETTINGS.equals(page)) {
            showSettings();
            return;
        }
        if (PAGE_INBOUND.equals(page)) {
            showInbound();
            return;
        }
        if (PAGE_OUTBOUND.equals(page)) {
            showOutbound();
            return;
        }
        showHome();
    }

    private void refreshDashboard(boolean renderHome) {
        refreshDashboard(renderHome, false);
    }

    private void refreshDashboard(boolean renderHome, boolean notify) {
        request("GET", "/dashboard", null, json -> {
            dashboard = json;
            parseDashboard(json);
            if (renderHome && PAGE_HOME.equals(currentPage)) {
                showHome();
            }
            if (notify) {
                toast("刷新成功");
            }
        }, error -> toast((notify ? "刷新失败：" : "后台连接失败：") + error));
    }

    private boolean shouldRefreshBeforeRender(String page) {
        return PAGE_INBOUND.equals(page) || PAGE_OUTBOUND.equals(page);
    }

    private void refreshAndRenderPage(String page) {
        showLoadingPage(page);
        request("GET", "/dashboard", null, json -> {
            dashboard = json;
            parseDashboard(json);
            if (page.equals(currentPage)) {
                renderPage(page);
            }
        }, error -> {
            toast("刷新失败：" + error);
            if (page.equals(currentPage)) {
                renderPage(page);
            }
        });
    }

    private void showLoadingPage(String page) {
        currentPage = page;
        outboundLabelInput = null;
        LinearLayout layout = pageRoot();
        layout.addView(title(pageTitle(page), "正在刷新后台数据，请稍候"));
        layout.addView(backButton());
        setContentView(wrap(layout));
    }

    private String pageTitle(String page) {
        if (PAGE_INBOUND.equals(page)) {
            return "入库";
        }
        if (PAGE_OUTBOUND.equals(page)) {
            return "出库";
        }
        if (PAGE_SETTINGS.equals(page)) {
            return "设置";
        }
        return "大北库存";
    }

    private void parseDashboard(JSONObject json) {
        products.clear();
        labels.clear();
        reasons.clear();
        personnel.clear();

        JSONArray productArray = json.optJSONArray("products");
        if (productArray != null) {
            for (int i = 0; i < productArray.length(); i++) {
                JSONObject item = productArray.optJSONObject(i);
                products.add(new ProductOption(
                        item.optString("skuId"),
                        item.optString("name"),
                        item.optInt("availableStock")
                ));
            }
        }

        JSONObject system = json.optJSONObject("inventorySystem");
        if (system != null) {
            JSONArray labelArray = system.optJSONArray("labels");
            if (labelArray != null) {
                for (int i = 0; i < labelArray.length(); i++) {
                    JSONObject item = labelArray.optJSONObject(i);
                    if ("in_stock".equals(item.optString("status"))) {
                        labels.add(new LabelOption(
                                item.optString("labelCode"),
                                item.optString("productName")
                        ));
                    }
                }
            }

            JSONArray reasonArray = system.optJSONArray("labelOutboundReasons");
            if (reasonArray != null) {
                for (int i = 0; i < reasonArray.length(); i++) {
                    JSONObject item = reasonArray.optJSONObject(i);
                    reasons.add(new ReasonOption(item.optString("id"), item.optString("name")));
                }
            }

            JSONArray personnelArray = system.optJSONArray("personnel");
            if (personnelArray != null) {
                for (int i = 0; i < personnelArray.length(); i++) {
                    JSONObject item = personnelArray.optJSONObject(i);
                    String name = item == null ? "" : item.optString("name").trim();
                    if (!name.isEmpty() && !personnel.contains(name)) {
                        personnel.add(name);
                    }
                }
            }
        }

        JSONArray dashboardPersonnelArray = json.optJSONArray("personnel");
        if (dashboardPersonnelArray != null) {
            for (int i = 0; i < dashboardPersonnelArray.length(); i++) {
                JSONObject item = dashboardPersonnelArray.optJSONObject(i);
                String name = item == null ? "" : item.optString("name").trim();
                if (!name.isEmpty() && !personnel.contains(name)) {
                    personnel.add(name);
                }
            }
        }
    }

    private void request(String method, String path, JSONObject body, SuccessCallback success, ErrorCallback failure) {
        executor.execute(() -> {
            try {
                URL url = new URL(apiBase() + path);
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod(method);
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(8000);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                if (body != null) {
                    connection.setDoOutput(true);
                    try (OutputStream output = connection.getOutputStream()) {
                        output.write(body.toString().getBytes(StandardCharsets.UTF_8));
                    }
                }

                int code = connection.getResponseCode();
                InputStream stream = code >= 200 && code < 300 ? connection.getInputStream() : connection.getErrorStream();
                String text = readAll(stream);
                JSONObject json = text.isEmpty() ? new JSONObject() : new JSONObject(text);
                mainHandler.post(() -> {
                    if (code >= 200 && code < 300) {
                        success.onSuccess(json);
                    } else {
                        failure.onError(json.optString("detail", text));
                    }
                });
            } catch (Exception error) {
                mainHandler.post(() -> failure.onError(error.getMessage()));
            }
        });
    }

    private String readAll(InputStream stream) throws Exception {
        if (stream == null) {
            return "";
        }
        BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
        StringBuilder builder = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            builder.append(line);
        }
        return builder.toString();
    }

    private String apiBase() {
        String host = prefs().getString("host", "10.0.2.2");
        int port = prefs().getInt("port", 4000);
        String apiPath = prefs().getString("apiPath", "/api");
        return "http://" + host + ":" + port + apiPath;
    }

    private SharedPreferences prefs() {
        return getSharedPreferences("server-config", MODE_PRIVATE);
    }

    private String summaryText() {
        if (dashboard == null) {
            return "尚未连接后台";
        }
        JSONObject metrics = dashboard.optJSONObject("metrics");
        JSONObject system = dashboard.optJSONObject("inventorySystem");
        JSONObject labelStats = system == null ? null : system.optJSONObject("labelStats");
        StringBuilder builder = new StringBuilder();
        builder.append("单量：").append(metrics == null ? 0 : metrics.optInt("totalOrders")).append("\n");
        builder.append("库存数：").append(metrics == null ? 0 : metrics.optInt("totalInventory")).append("\n");
        builder.append("在库标签：").append(labelStats == null ? 0 : labelStats.optInt("inStock")).append("\n");
        builder.append("已出库标签：").append(labelStats == null ? 0 : labelStats.optInt("outbound")).append("\n\n");
        for (ProductOption product : products) {
            builder.append(product.name).append("：").append(product.stock).append(" 个\n");
        }
        return builder.toString();
    }

    private String formatInboundResult(JSONObject json, int count) {
        JSONObject product = json.optJSONObject("product");
        JSONArray qrCodes = json.optJSONArray("labels");
        StringBuilder builder = new StringBuilder();
        builder.append("入库完成\n");
        builder.append("产品：").append(product == null ? "" : product.optString("name")).append("\n");
        builder.append("当前库存：").append(product == null ? 0 : product.optInt("availableStock")).append("\n");
        builder.append("二维码数量：").append(count).append("\n\n");
        if (qrCodes != null) {
            for (int i = 0; i < qrCodes.length(); i++) {
                builder.append(qrCodes.optJSONObject(i).optString("labelCode")).append("\n");
            }
        }
        return builder.toString();
    }

    private String formatOutboundResult(JSONObject json) {
        JSONObject label = json.optJSONObject("label");
        JSONObject product = json.optJSONObject("product");
        return "出库完成\n"
                + "标签：" + (label == null ? "" : label.optString("labelCode")) + "\n"
                + "原因：" + (label == null ? "" : label.optString("outboundReason")) + "\n"
                + "产品库存：" + (product == null ? 0 : product.optInt("availableStock")) + "\n"
                + "状态：已剪标";
    }

    private void handleOutboundError(String error) {
        if (error != null && (error.contains("已出库") || error.contains("重复出库"))) {
            new AlertDialog.Builder(this)
                    .setMessage("已出库，请勿重复操作")
                    .setPositiveButton("知道了", null)
                    .show();
            return;
        }
        toast("出库失败：" + error);
    }

    private List<String> productNames() {
        List<String> names = new ArrayList<>();
        for (ProductOption product : products) {
            names.add(product.name);
        }
        if (names.isEmpty()) {
            names.add("暂无产品");
        }
        return names;
    }

    private List<String> productSearchLabels(String query) {
        String normalizedQuery = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        List<String> labels = new ArrayList<>();
        for (ProductOption product : products) {
            String label = formatProductOption(product);
            if (normalizedQuery.isEmpty()
                    || label.toLowerCase(Locale.ROOT).contains(normalizedQuery)
                    || product.name.toLowerCase(Locale.ROOT).contains(normalizedQuery)
                    || product.skuId.toLowerCase(Locale.ROOT).contains(normalizedQuery)) {
                labels.add(label);
            }
        }
        if (labels.isEmpty()) {
            labels.add("暂无匹配产品");
        }
        return labels;
    }

    private ProductOption resolveProductSelection(String text) {
        if (text == null) {
            return null;
        }
        String normalized = text.trim();
        for (ProductOption product : products) {
            if (normalized.equals(formatProductOption(product))
                    || normalized.equals(product.name)
                    || normalized.equals(product.skuId)
                    || normalized.startsWith(product.name + " · ")
                    || normalized.contains(" · " + product.skuId + " · ")) {
                return product;
            }
        }
        return null;
    }

    private String formatProductOption(ProductOption product) {
        return product.name + " · " + product.skuId + " · " + product.stock + "件";
    }

    private List<String> labelNames() {
        List<String> names = new ArrayList<>();
        for (LabelOption label : labels) {
            names.add(label.labelCode + " · " + label.productName);
        }
        return names;
    }

    private List<String> reasonNames() {
        List<String> names = new ArrayList<>();
        for (ReasonOption reason : reasons) {
            names.add(reason.name);
        }
        if (names.isEmpty()) {
            names.add("懂茶帝发货");
            reasons.add(new ReasonOption("dongchadi", "懂茶帝发货"));
        }
        return names;
    }

    private List<String> personnelNames() {
        List<String> names = new ArrayList<>(personnel);
        if (names.isEmpty()) {
            names.add("小梅雨");
            names.add("六一");
        }
        return names;
    }

    private ScrollView wrap(View view) {
        ScrollView scrollView = new ScrollView(this);
        scrollView.setBackgroundColor(BG);
        scrollView.addView(view);
        int baseLeft = view.getPaddingLeft();
        int baseTop = view.getPaddingTop();
        int baseRight = view.getPaddingRight();
        int baseBottom = view.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(scrollView, (root, insets) -> {
            Insets systemBars = insets.getInsets(
                    WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.displayCutout()
            );
            view.setPadding(
                    baseLeft + systemBars.left,
                    baseTop + systemBars.top + dp(8),
                    baseRight + systemBars.right,
                    baseBottom + systemBars.bottom
            );
            return insets;
        });
        ViewCompat.requestApplyInsets(scrollView);
        return scrollView;
    }

    private LinearLayout pageRoot() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int padding = dp(18);
        layout.setPadding(padding, padding, padding, padding);
        return layout;
    }

    private LinearLayout title(String title, String subtitle) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(0, 0, 0, dp(14));
        TextView titleView = new TextView(this);
        titleView.setText(title);
        titleView.setTextColor(TEXT);
        titleView.setTextSize(28);
        titleView.setGravity(Gravity.START);
        titleView.setTypeface(null, android.graphics.Typeface.BOLD);
        box.addView(titleView);
        TextView subtitleView = new TextView(this);
        subtitleView.setText(subtitle);
        subtitleView.setTextColor(MUTED);
        subtitleView.setTextSize(14);
        subtitleView.setPadding(0, dp(6), 0, 0);
        box.addView(subtitleView);
        return box;
    }

    private TextView sectionTitle(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(TEXT);
        view.setTextSize(18);
        view.setTypeface(null, android.graphics.Typeface.BOLD);
        view.setPadding(0, dp(18), 0, dp(8));
        return view;
    }

    private TextView label(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(MUTED);
        view.setTextSize(14);
        view.setPadding(0, dp(12), 0, dp(6));
        return view;
    }

    private TextView hintText(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(MUTED);
        view.setTextSize(12);
        view.setPadding(0, 0, 0, dp(8));
        return view;
    }

    private TextView bodyText(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(TEXT);
        view.setTextSize(14);
        view.setLineSpacing(dp(3), 1.0f);
        view.setPadding(dp(12), dp(12), dp(12), dp(12));
        view.setBackgroundColor(Color.WHITE);
        return view;
    }

    private EditText input(String hint) {
        EditText input = new EditText(this);
        input.setHint(hint);
        input.setSingleLine(true);
        input.setTextSize(16);
        input.setPadding(dp(12), 0, dp(12), 0);
        input.setMinHeight(dp(48));
        input.setBackgroundColor(Color.WHITE);
        input.setLayoutParams(blockParams());
        return input;
    }

    private AutoCompleteTextView productSearchInput() {
        AutoCompleteTextView input = new AutoCompleteTextView(this);
        input.setHint("输入产品名称或 SKU 搜索");
        input.setSingleLine(true);
        input.setTextSize(16);
        input.setPadding(dp(12), 0, dp(12), 0);
        input.setMinHeight(dp(48));
        input.setThreshold(0);
        input.setBackgroundColor(Color.WHITE);
        input.setLayoutParams(blockParams());

        input.setAdapter(productSearchAdapter());
        input.setOnClickListener(view -> input.showDropDown());
        input.setOnFocusChangeListener((view, hasFocus) -> {
            if (hasFocus) {
                input.showDropDown();
            }
        });
        return input;
    }

    private ArrayAdapter<String> productSearchAdapter() {
        return new ArrayAdapter<String>(
                this,
                android.R.layout.simple_dropdown_item_1line,
                productSearchLabels("")
        ) {
            @Override
            public Filter getFilter() {
                return new Filter() {
                    @Override
                    protected FilterResults performFiltering(CharSequence constraint) {
                        List<String> matches = productSearchLabels(constraint == null ? "" : constraint.toString());
                        FilterResults results = new FilterResults();
                        results.values = matches;
                        results.count = matches.size();
                        return results;
                    }

                    @Override
                    protected void publishResults(CharSequence constraint, FilterResults results) {
                        clear();
                        if (results.values instanceof List<?>) {
                            for (Object value : (List<?>) results.values) {
                                add(String.valueOf(value));
                            }
                        }
                        notifyDataSetChanged();
                    }
                };
            }
        };
    }

    private Spinner spinner(List<String> values) {
        Spinner spinner = new Spinner(this);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, values);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
        spinner.setMinimumHeight(dp(48));
        spinner.setLayoutParams(blockParams());
        return spinner;
    }

    private Button primaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(16);
        button.setAllCaps(false);
        button.setBackgroundColor(GREEN);
        button.setMinHeight(dp(48));
        button.setLayoutParams(blockParams());
        return button;
    }

    private Button secondaryButton(String text) {
        Button button = primaryButton(text);
        button.setTextColor(TEXT);
        button.setBackgroundColor(Color.WHITE);
        return button;
    }

    private Button backButton() {
        Button button = secondaryButton("返回");
        button.setOnClickListener(view -> {
            if (!navigateBack()) {
                showHome();
            }
        });
        return button;
    }

    private LinearLayout.LayoutParams blockParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(6), 0, dp(6));
        return params;
    }

    private void toast(String text) {
        Toast.makeText(this, text, Toast.LENGTH_SHORT).show();
    }

    private int parseInt(String text) {
        try {
            return Integer.parseInt(text);
        } catch (NumberFormatException error) {
            return 0;
        }
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private List<String> listOf(String... values) {
        List<String> list = new ArrayList<>();
        for (String value : values) {
            list.add(value);
        }
        return list;
    }

    private interface SuccessCallback {
        void onSuccess(JSONObject json);
    }

    private interface ErrorCallback {
        void onError(String error);
    }

    private static final class ProductOption {
        final String skuId;
        final String name;
        final int stock;

        ProductOption(String skuId, String name, int stock) {
            this.skuId = skuId;
            this.name = name;
            this.stock = stock;
        }
    }

    private static final class LabelOption {
        final String labelCode;
        final String productName;

        LabelOption(String labelCode, String productName) {
            this.labelCode = labelCode;
            this.productName = productName;
        }
    }

    private static final class ReasonOption {
        final String id;
        final String name;

        ReasonOption(String id, String name) {
            this.id = id;
            this.name = name;
        }
    }
}
