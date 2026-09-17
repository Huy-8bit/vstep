import { SkillSwitch } from "@/features/speaking/skill-switch";
import { ProgressView } from "@/features/progress/progress-view";
export default function ProgressPage() {
  return (
    <>
      <SkillSwitch section="progress" active="writing" />
      <ProgressView />
    </>
  );
}
