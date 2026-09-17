import { SkillSwitch } from "@/features/speaking/skill-switch";
import { HistoryView } from "@/features/history/history-view";
export default function HistoryPage() {
  return (
    <>
      <SkillSwitch section="history" active="writing" />
      <HistoryView />
    </>
  );
}
