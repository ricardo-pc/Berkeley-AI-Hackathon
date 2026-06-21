import { redirect } from "next/navigation";

// No sign-in step in the demo — land straight on the patient lookup.
export default function Home() {
  redirect("/ehr");
}
