import { describe, expect, it } from "vitest";

import { formatElapsed, parseServerTimestamp } from "./time";

describe("parseServerTimestamp", () => {
  it("returns null for empty values", () => {
    expect(parseServerTimestamp(null)).toBeNull();
    expect(parseServerTimestamp("")).toBeNull();
  });

  it("treats timezone-naive timestamps as UTC", () => {
    const naive = "2026-03-23T00:00:00";
    const expected = Date.parse("2026-03-23T00:00:00Z");

    expect(parseServerTimestamp(naive)).toBe(expected);
  });

  it("preserves explicit timezone offsets", () => {
    const withOffset = "2026-03-23T08:00:00+08:00";
    const expected = Date.parse(withOffset);

    expect(parseServerTimestamp(withOffset)).toBe(expected);
  });
});

describe("formatElapsed", () => {
  it("formats null as 00:00", () => {
    expect(formatElapsed(null)).toBe("00:00");
  });

  it("formats seconds correctly", () => {
    expect(formatElapsed(1_000)).toBe("00:01");
    expect(formatElapsed(61_000)).toBe("01:01");
  });

  it("keeps strict mm:ss even for long durations", () => {
    expect(formatElapsed(3_661_000)).toBe("61:01");
  });
});
