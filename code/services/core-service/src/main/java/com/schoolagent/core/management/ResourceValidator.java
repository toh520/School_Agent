package com.schoolagent.core.management;

import com.schoolagent.core.management.ManagementDtos.FieldError;
import java.math.BigDecimal;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;

/** Performs field, duplicate and reference validation before every M03 write. */
@Component
class ResourceValidator {

  private static final Pattern CODE = Pattern.compile("[A-Z0-9][A-Z0-9_-]{2,39}");
  private static final Pattern ISBN = Pattern.compile("(?:97[89])?[0-9]{9}[0-9X]");

  private final ManagementRepository repository;

  ResourceValidator(ManagementRepository repository) {
    this.repository = repository;
  }

  ValidationResult validate(ResourceType type, Map<String, ?> rawValues, UUID excludedId, int row) {
    List<FieldError> errors = new ArrayList<>();
    Map<String, Object> normalized = new LinkedHashMap<>();
    List<FieldDefinition> fields = ResourceSchema.fields(type);
    Set<String> allowed =
        fields.stream().map(FieldDefinition::key).collect(java.util.stream.Collectors.toSet());
    rawValues.keySet().stream()
        .filter(key -> !allowed.contains(key))
        .forEach(key -> errors.add(error(row, key, "字段不在当前资料模板中")));

    for (FieldDefinition field : fields) {
      Object raw = rawValues.get(field.key());
      if (blank(raw)) {
        if (field.required()) {
          errors.add(error(row, field.key(), field.label() + "为必填项"));
        }
        continue;
      }
      try {
        normalized.put(field.key(), normalize(field, raw));
      } catch (IllegalArgumentException exception) {
        errors.add(error(row, field.key(), exception.getMessage()));
      }
    }

    validateCommon(type, normalized, excludedId, row, errors);
    validateDomain(type, normalized, row, errors);
    return new ValidationResult(normalized, errors, completeness(fields, normalized));
  }

  private Object normalize(FieldDefinition field, Object raw) {
    return switch (field.kind()) {
      case INTEGER -> integer(raw, field.label());
      case DECIMAL -> decimal(raw, field.label());
      case URL -> url(raw, field.label());
      case LIST -> list(raw);
      case SELECT -> selection(field, raw);
      case TEXT, LONG_TEXT -> text(raw, field.kind() == FieldKind.LONG_TEXT ? 20_000 : 1_000);
    };
  }

  private void validateCommon(
      ResourceType type,
      Map<String, Object> values,
      UUID excludedId,
      int row,
      List<FieldError> errors) {
    String code = string(values.get("code"));
    if (code != null) {
      code = code.toUpperCase(Locale.ROOT);
      values.put("code", code);
      if (!CODE.matcher(code).matches()) {
        errors.add(error(row, "code", "编码需为3–40位大写字母、数字、下划线或连字符"));
      } else if (repository.existsCode(type, code, excludedId)) {
        errors.add(error(row, "code", "编码已存在"));
      }
    }
    if (type.parentType() != null) {
      String parentCode = string(values.get(type.parentField()));
      if (parentCode != null) {
        parentCode = parentCode.toUpperCase(Locale.ROOT);
        values.put(type.parentField(), parentCode);
        if (!repository.existsCode(type.parentType(), parentCode, null)) {
          errors.add(
              error(row, type.parentField(), "引用的" + type.parentType().displayName() + "不存在"));
        }
      }
    }
  }

  private void validateDomain(
      ResourceType type, Map<String, Object> values, int row, List<FieldError> errors) {
    switch (type) {
      case INGREDIENT -> nonNegative(values, row, errors, "nutritionKcal", "nutritionProtein");
      case DISH -> validateDish(values, row, errors);
      case BOOK -> validateBook(values, row, errors);
      case HOLDING -> validateHolding(values, row, errors);
      case SYSTEM_CONFIG -> validateConfig(values, row, errors);
      default -> {
        // Common validation is sufficient for canteens and stalls.
      }
    }
  }

  private void validateDish(Map<String, Object> values, int row, List<FieldError> errors) {
    nonNegative(values, row, errors, "price", "nutritionKcal", "nutritionProtein");
    Object codes = values.get("ingredientCodes");
    if (codes instanceof List<?> ingredients) {
      for (Object ingredient : ingredients) {
        String code = String.valueOf(ingredient).toUpperCase(Locale.ROOT);
        if (!repository.existsCode(ResourceType.INGREDIENT, code, null)) {
          errors.add(error(row, "ingredientCodes", "食材编码不存在：" + code));
        }
      }
    }
  }

  private void validateBook(Map<String, Object> values, int row, List<FieldError> errors) {
    String isbn = string(values.get("isbn"));
    if (isbn != null && !ISBN.matcher(isbn.replace("-", "")).matches()) {
      errors.add(error(row, "isbn", "ISBN 应为10位或13位数字"));
    }
    Integer year = integerValue(values.get("publishedYear"));
    if (year != null && (year < 1000 || year > 2100)) {
      errors.add(error(row, "publishedYear", "出版年份需在1000至2100之间"));
    }
  }

  private void validateHolding(Map<String, Object> values, int row, List<FieldError> errors) {
    Integer total = integerValue(values.get("totalCount"));
    Integer available = integerValue(values.get("availableCount"));
    if (total != null && total < 0) {
      errors.add(error(row, "totalCount", "总册数不能为负数"));
    }
    if (available != null && available < 0) {
      errors.add(error(row, "availableCount", "可借册数不能为负数"));
    }
    if (total != null && available != null && available > total) {
      errors.add(error(row, "availableCount", "可借册数不能超过总册数"));
    }
  }

  private void validateConfig(Map<String, Object> values, int row, List<FieldError> errors) {
    String code = string(values.get("code"));
    if (code == null) {
      return;
    }
    String upper = code.toUpperCase(Locale.ROOT);
    if (List.of("PASSWORD", "SECRET", "TOKEN", "CREDENTIAL", "PRIVATE_KEY", "API_KEY").stream()
        .anyMatch(upper::contains)) {
      errors.add(error(row, "code", "敏感配置必须使用环境变量，不能在后台保存"));
    }
  }

  private void nonNegative(
      Map<String, Object> values, int row, List<FieldError> errors, String... fields) {
    for (String field : fields) {
      Object value = values.get(field);
      if (value instanceof BigDecimal number && number.signum() < 0) {
        errors.add(error(row, field, "数值不能为负数"));
      }
    }
  }

  private int completeness(List<FieldDefinition> fields, Map<String, Object> values) {
    List<FieldDefinition> tracked =
        fields.stream().filter(field -> field.required() || field.recommended()).toList();
    long filled = tracked.stream().filter(field -> !blank(values.get(field.key()))).count();
    return tracked.isEmpty() ? 100 : (int) Math.round(filled * 100.0 / tracked.size());
  }

  private String selection(FieldDefinition field, Object raw) {
    String value = text(raw, 100).toUpperCase(Locale.ROOT);
    if (!field.options().contains(value)) {
      throw new IllegalArgumentException(field.label() + "取值无效");
    }
    return value;
  }

  private List<String> list(Object raw) {
    Collection<?> values =
        raw instanceof Collection<?> collection
            ? collection
            : List.of(String.valueOf(raw).split("\\|"));
    return values.stream()
        .map(String::valueOf)
        .map(String::trim)
        .filter(value -> !value.isBlank())
        .distinct()
        .limit(50)
        .toList();
  }

  private String url(Object raw, String label) {
    String value = text(raw, 1_000);
    URI uri;
    try {
      uri = URI.create(value);
    } catch (IllegalArgumentException exception) {
      throw new IllegalArgumentException(label + "格式无效", exception);
    }
    if (!("http".equalsIgnoreCase(uri.getScheme()) || "https".equalsIgnoreCase(uri.getScheme()))
        || uri.getHost() == null) {
      throw new IllegalArgumentException(label + "仅允许 HTTP/HTTPS 地址");
    }
    return value;
  }

  private int integer(Object raw, String label) {
    try {
      return Integer.parseInt(String.valueOf(raw).trim());
    } catch (NumberFormatException exception) {
      throw new IllegalArgumentException(label + "需填写整数", exception);
    }
  }

  private BigDecimal decimal(Object raw, String label) {
    try {
      return new BigDecimal(String.valueOf(raw).trim());
    } catch (NumberFormatException exception) {
      throw new IllegalArgumentException(label + "需填写数字", exception);
    }
  }

  private String text(Object raw, int maxLength) {
    String value = String.valueOf(raw).trim();
    if (value.length() > maxLength) {
      throw new IllegalArgumentException("内容超过" + maxLength + "个字符");
    }
    return value;
  }

  private Integer integerValue(Object value) {
    return value instanceof Integer number ? number : null;
  }

  private String string(Object value) {
    return value == null ? null : String.valueOf(value);
  }

  private boolean blank(Object value) {
    return value == null
        || (value instanceof String text && text.isBlank())
        || (value instanceof Collection<?> collection && collection.isEmpty());
  }

  private FieldError error(int row, String field, String message) {
    return new FieldError(row, field, message);
  }
}
