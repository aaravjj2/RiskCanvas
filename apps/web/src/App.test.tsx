import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders app title", () => {
  render(<App />);
  expect(screen.getByTestId("title")).toHaveTextContent("RiskCanvas");
});

test("renders app description", () => {
  render(<App />);
  expect(screen.getByText("Deterministic risk preview.")).toBeInTheDocument();
});