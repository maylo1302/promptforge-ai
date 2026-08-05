import { describe, expect, it } from "vitest";
import { cn } from "./utils";

describe("cn", () => {
  it("scala klasy Tailwind bez konfliktów", () => {
    expect(cn("p-2", "p-4", "text-sm")).toBe("p-4 text-sm");
  });
});
