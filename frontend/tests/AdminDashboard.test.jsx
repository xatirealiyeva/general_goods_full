import React from "react";
import {
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import AdminDashboard from "../src/pages/AdminDashboard.jsx";
import client from "../src/api/client.js";

vi.mock("../src/api/client.js", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

const mockResponses = [
  {
    data: [
      {
        id: 1,
        name: "Electronics",
        status: "ACTIVE",
      },
    ],
  },
  {
    data: [
      {
        id: 1,
        email: "admin@example.com",
        account_status: "ACTIVE",
      },
    ],
  },
  {
    data: [
      {
        id: 1,
        order_number: "ORD-001",
        status: "PENDING",
      },
    ],
  },
  {
    data: [],
  },
  {
    data: [],
  },
  {
    data: [
      {
        id: 1,
        sku: "PHONE-001",
        stock_quantity: 2,
      },
    ],
  },
  {
    data: [
      {
        id: 1,
        code: "SAVE10",
        discount_type: "PERCENTAGE",
        value: "10.00",
        is_active: true,
        starts_at: "2026-08-26T00:00:00Z",
        ends_at: "2026-12-31T00:00:00Z",
      },
    ],
  },
  {
    data: [
      {
        id: 1,
        name: "Baku Zone",
        regions: ["Baku", "Sumqayit"],
        delivery_fee: "5.00",
        estimated_days: 2,
        is_active: true,
      },
    ],
  },
];

beforeEach(() => {
  vi.clearAllMocks();

  client.get.mockImplementation(
    async (url) => {
      const endpoints = [
        "/catalog/categories/",
        "/users/",
        "/orders/admin/",
        "/orders/refund-requests/admin/",
        "/orders/disputes/admin/",
        "/inventory/low-stock/",
        "/catalog/discount-codes/",
        "/shipments/zones/",
      ];

      const index = endpoints.indexOf(url);

      return mockResponses[index] || {
        data: [],
      };
    }
  );

  client.post.mockResolvedValue({
    data: {},
  });

  client.patch.mockResolvedValue({
    data: {},
  });
});

describe("AdminDashboard", () => {
  it("renders administration dashboard", async () => {
    render(<AdminDashboard />);

    expect(
      screen.getByText("Store management")
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText("Electronics")
      ).toBeInTheDocument();
    });
  });

  it("loads users and orders", async () => {
    render(<AdminDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("admin@example.com")
      ).toBeInTheDocument();

      expect(
        screen.getByText("ORD-001")
      ).toBeInTheDocument();
    });
  });

  it("displays discount codes", async () => {
    render(<AdminDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("SAVE10")
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Discount codes")
    ).toBeInTheDocument();
  });

  it("displays shipping zones", async () => {
    render(<AdminDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("Baku Zone")
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        /Baku, Sumqayit/
      )
    ).toBeInTheDocument();
  });

  it("displays low stock products", async () => {
    render(<AdminDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText(/PHONE-001/)
      ).toBeInTheDocument();
    });
  });

  it("creates a discount code", async () => {
    render(<AdminDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("SAVE10")
      ).toBeInTheDocument();
    });

    const codeInput =
      screen.getByPlaceholderText(
        "Discount code"
      );

    expect(codeInput).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Create discount code",
      })
    ).toBeInTheDocument();
  });

  it("creates a shipping zone", async () => {
    render(<AdminDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("Baku Zone")
      ).toBeInTheDocument();
    });

    expect(
      screen.getByPlaceholderText(
        "Zone name"
      )
    ).toBeInTheDocument();

    expect(
      screen.getByPlaceholderText(
        /Regions, e.g./
      )
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Create shipping zone",
      })
    ).toBeInTheDocument();
  });
});