import { PatientChartShell } from "../../_components/PatientChartShell";
import { PatientProvider } from "../../_components/PatientContext";

export default function PatientChartLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <PatientProvider>
      <PatientChartShell>{children}</PatientChartShell>
    </PatientProvider>
  );
}
