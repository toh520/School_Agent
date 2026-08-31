package com.schoolagent.core.management;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

/** Small RFC-4180-style parser for bounded M03 UTF-8 CSV imports. */
@Component
class CsvTableParser {

  List<Map<String, String>> parse(String content) {
    List<List<String>> rows = parseRows(content.replace("\r\n", "\n").replace('\r', '\n'));
    if (rows.isEmpty()) {
      return List.of();
    }
    List<String> headers = rows.getFirst().stream().map(String::trim).toList();
    if (headers.isEmpty() || headers.stream().anyMatch(String::isBlank)) {
      throw new IllegalArgumentException("CSV header contains an empty field");
    }
    if (headers.stream().distinct().count() != headers.size()) {
      throw new IllegalArgumentException("CSV header contains duplicate fields");
    }

    List<Map<String, String>> result = new ArrayList<>();
    for (int rowIndex = 1; rowIndex < rows.size(); rowIndex++) {
      List<String> row = rows.get(rowIndex);
      if (row.stream().allMatch(String::isBlank)) {
        continue;
      }
      if (row.size() != headers.size()) {
        throw new IllegalArgumentException("CSV row " + (rowIndex + 1) + " has wrong column count");
      }
      Map<String, String> values = new LinkedHashMap<>();
      for (int column = 0; column < headers.size(); column++) {
        values.put(headers.get(column), row.get(column).trim());
      }
      result.add(values);
    }
    if (result.size() > 200) {
      throw new IllegalArgumentException("CSV import is limited to 200 records");
    }
    return result;
  }

  private List<List<String>> parseRows(String content) {
    List<List<String>> rows = new ArrayList<>();
    List<String> row = new ArrayList<>();
    StringBuilder field = new StringBuilder();
    boolean quoted = false;
    for (int index = 0; index < content.length(); index++) {
      char current = content.charAt(index);
      if (current == '"') {
        if (quoted && index + 1 < content.length() && content.charAt(index + 1) == '"') {
          field.append('"');
          index++;
        } else {
          quoted = !quoted;
        }
      } else if (current == ',' && !quoted) {
        row.add(field.toString());
        field.setLength(0);
      } else if (current == '\n' && !quoted) {
        row.add(field.toString());
        rows.add(row);
        row = new ArrayList<>();
        field.setLength(0);
      } else {
        field.append(current);
      }
    }
    if (quoted) {
      throw new IllegalArgumentException("CSV contains an unclosed quote");
    }
    if (!field.isEmpty() || !row.isEmpty()) {
      row.add(field.toString());
      rows.add(row);
    }
    return rows;
  }
}
