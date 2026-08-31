package com.schoolagent.core.management;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** Authoritative M03 field catalog used by API, UI and CSV import validation. */
public final class ResourceSchema {

  private static final Map<ResourceType, List<FieldDefinition>> SCHEMAS = buildSchemas();

  private ResourceSchema() {}

  public static List<FieldDefinition> fields(ResourceType type) {
    return SCHEMAS.get(type);
  }

  private static Map<ResourceType, List<FieldDefinition>> buildSchemas() {
    Map<ResourceType, List<FieldDefinition>> schemas = new EnumMap<>(ResourceType.class);
    schemas.put(
        ResourceType.CANTEEN,
        fields(
            required("code", "食堂编码", FieldKind.TEXT, "稳定唯一编码，如 CANTEEN-NORTH"),
            required("name", "食堂名称", FieldKind.TEXT, "对学生展示的正式名称"),
            recommended("location", "位置", FieldKind.TEXT, "校区、楼栋或生活区"),
            recommended("openingHours", "开放时间", FieldKind.TEXT, "例如 06:30-20:30"),
            optional("description", "说明", FieldKind.LONG_TEXT, "服务范围或楼层说明"),
            required("source", "信息来源", FieldKind.TEXT, "公开公示或责任部门")));
    schemas.put(
        ResourceType.STALL,
        fields(
            required("code", "窗口编码", FieldKind.TEXT, "稳定唯一编码"),
            required("name", "窗口名称", FieldKind.TEXT, "窗口公示名称"),
            required("canteenCode", "所属食堂编码", FieldKind.TEXT, "必须引用已存在的食堂"),
            recommended("location", "位置", FieldKind.TEXT, "楼层或区域"),
            recommended("openingHours", "供应时间", FieldKind.TEXT, "窗口营业时间"),
            required("source", "信息来源", FieldKind.TEXT, "公开公示或责任部门")));
    schemas.put(
        ResourceType.INGREDIENT,
        fields(
            required("code", "食材编码", FieldKind.TEXT, "稳定唯一编码"),
            required("name", "食材名称", FieldKind.TEXT, "通用食材名称"),
            recommended("category", "分类", FieldKind.TEXT, "蔬菜、肉类、主食等"),
            recommended("taste", "口味特征", FieldKind.TEXT, "清淡、辛辣、酸甜等"),
            recommended("nutritionKcal", "热量（千卡/100克）", FieldKind.DECIMAL, "非负数"),
            recommended("nutritionProtein", "蛋白质（克/100克）", FieldKind.DECIMAL, "非负数"),
            recommended("allergens", "过敏原", FieldKind.LIST, "多项使用竖线分隔"),
            required("source", "信息来源", FieldKind.TEXT, "食品公示或公开资料")));
    schemas.put(
        ResourceType.DISH,
        fields(
            required("code", "菜品编码", FieldKind.TEXT, "稳定唯一编码"),
            required("name", "菜品名称", FieldKind.TEXT, "菜单公示名称"),
            required("stallCode", "所属窗口编码", FieldKind.TEXT, "必须引用已存在窗口"),
            required("price", "价格", FieldKind.DECIMAL, "人民币金额，不能为负数"),
            optional("imageUrl", "图片地址", FieldKind.URL, "仅允许 HTTP/HTTPS 地址"),
            recommended("tastes", "口味", FieldKind.LIST, "多项使用竖线分隔"),
            recommended("ingredientCodes", "食材编码", FieldKind.LIST, "引用已存在食材，使用竖线分隔"),
            recommended("nutritionKcal", "单份热量（千卡）", FieldKind.DECIMAL, "非负数"),
            recommended("nutritionProtein", "单份蛋白质（克）", FieldKind.DECIMAL, "非负数"),
            recommended("allergens", "过敏原", FieldKind.LIST, "蛋类、奶类、坚果等"),
            recommended("supplyPeriods", "供应时段", FieldKind.LIST, "早餐、午餐、晚餐"),
            select(
                "availabilityStatus", "供应状态", true, List.of("AVAILABLE", "UNAVAILABLE"), "是否可供应"),
            required("source", "信息来源", FieldKind.TEXT, "菜单或窗口公示")));
    schemas.put(
        ResourceType.BOOK,
        fields(
            required("code", "书目编码", FieldKind.TEXT, "稳定唯一编码"),
            required("name", "书名", FieldKind.TEXT, "正式书名"),
            required("isbn", "ISBN", FieldKind.TEXT, "10位或13位 ISBN"),
            required("authors", "作者", FieldKind.LIST, "多位作者使用竖线分隔"),
            recommended("publisher", "出版社", FieldKind.TEXT, "出版机构"),
            recommended("edition", "版本", FieldKind.TEXT, "例如 第2版"),
            recommended("publishedYear", "出版年份", FieldKind.INTEGER, "四位年份"),
            recommended("language", "语言", FieldKind.TEXT, "中文、英文等"),
            recommended("summary", "简介", FieldKind.LONG_TEXT, "内容与适读对象"),
            recommended("tags", "主题标签", FieldKind.LIST, "多项使用竖线分隔"),
            recommended("difficulty", "难度", FieldKind.TEXT, "基础、进阶或专业"),
            required("source", "信息来源", FieldKind.TEXT, "图书馆或公开书目来源")));
    schemas.put(
        ResourceType.HOLDING,
        fields(
            required("code", "馆藏编码", FieldKind.TEXT, "稳定唯一编码"),
            required("name", "馆藏名称", FieldKind.TEXT, "便于后台识别"),
            required("bookCode", "书目编码", FieldKind.TEXT, "必须引用已存在书目"),
            required("callNumber", "索书号", FieldKind.TEXT, "馆藏检索号码"),
            required("location", "馆藏位置", FieldKind.TEXT, "馆、楼层和区域"),
            required("totalCount", "总册数", FieldKind.INTEGER, "不能为负数"),
            required("availableCount", "可借册数", FieldKind.INTEGER, "不能超过总册数"),
            select(
                "availabilityStatus", "可用状态", true, List.of("AVAILABLE", "UNAVAILABLE"), "当前是否可借"),
            required("source", "信息来源", FieldKind.TEXT, "图书馆馆藏系统或公示")));
    schemas.put(
        ResourceType.KNOWLEDGE,
        fields(
            required("code", "公告编码", FieldKind.TEXT, "稳定唯一编码，如 NOTICE-LIBRARY-01"),
            required("name", "公告标题", FieldKind.TEXT, "概括正文内容的标题"),
            required("category", "公告类别", FieldKind.TEXT, "例如办事指南、规章制度或活动通知"),
            required("keywords", "检索关键词", FieldKind.LIST, "供后续检索使用，多项以竖线分隔"),
            required("body", "公告正文", FieldKind.LONG_TEXT, "可直接作为后续问答依据的完整文字"),
            required("source", "信息来源", FieldKind.TEXT, "公告发布页面、文件或责任部门")));
    schemas.put(
        ResourceType.SYSTEM_CONFIG,
        fields(
            required("code", "配置键", FieldKind.TEXT, "只能保存非敏感公共配置"),
            required("name", "配置名称", FieldKind.TEXT, "管理员可识别的名称"),
            required("configValue", "配置值", FieldKind.LONG_TEXT, "禁止密码、密钥和令牌"),
            recommended("description", "用途说明", FieldKind.LONG_TEXT, "说明影响范围"),
            required("source", "配置依据", FieldKind.TEXT, "需求、制度或项目配置基线")));
    return Map.copyOf(schemas);
  }

  private static List<FieldDefinition> fields(FieldDefinition... fields) {
    return List.of(fields);
  }

  private static FieldDefinition required(String key, String label, FieldKind kind, String help) {
    return new FieldDefinition(key, label, kind, true, false, List.of(), help);
  }

  private static FieldDefinition recommended(
      String key, String label, FieldKind kind, String help) {
    return new FieldDefinition(key, label, kind, false, true, List.of(), help);
  }

  private static FieldDefinition optional(String key, String label, FieldKind kind, String help) {
    return new FieldDefinition(key, label, kind, false, false, List.of(), help);
  }

  private static FieldDefinition select(
      String key, String label, boolean required, List<String> options, String help) {
    return new FieldDefinition(key, label, FieldKind.SELECT, required, false, options, help);
  }
}
