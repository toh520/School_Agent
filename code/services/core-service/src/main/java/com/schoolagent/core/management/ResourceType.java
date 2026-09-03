package com.schoolagent.core.management;

/** Whitelisted M03 resource types; table names never come from request text. */
public enum ResourceType {
  CANTEEN("canteen", "食堂", null, null),
  STALL("food_stall", "窗口", CANTEEN, "canteenCode"),
  INGREDIENT("ingredient", "食材", null, null),
  DISH("dish", "餐品", null, null),
  BOOK("book", "书目", null, null),
  HOLDING("library_holding", "馆藏", BOOK, "bookCode"),
  KNOWLEDGE("knowledge_document", "校园知识库", null, null),
  SYSTEM_CONFIG("system_config", "公共配置", null, null);

  private final String tableName;
  private final String displayName;
  private final ResourceType parentType;
  private final String parentField;

  ResourceType(String tableName, String displayName, ResourceType parentType, String parentField) {
    this.tableName = tableName;
    this.displayName = displayName;
    this.parentType = parentType;
    this.parentField = parentField;
  }

  public String tableName() {
    return tableName;
  }

  public String displayName() {
    return displayName;
  }

  public ResourceType parentType() {
    return parentType;
  }

  public String parentField() {
    return parentField;
  }
}
