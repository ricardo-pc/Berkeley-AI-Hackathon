import { PatientChartShell } from "../../_components/PatientChartShell";
import { PatientProvider } from "../../_components/PatientContext";
import { getPatientBundle } from "../../_lib/ehr";

export default async function PatientChartLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const bundle = await getPatientBundle(id);

  return (
    <PatientProvider
      patient={bundle?.patient ?? null}
      providers={bundle?.providers ?? []}
    >
      <PatientChartShell>{children}</PatientChartShell>
    </PatientProvider>
  );
}
