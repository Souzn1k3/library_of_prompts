import { MissionDetailClient } from "@/components/MissionDetailClient";

type Props = {
  params: Promise<{ slug: string }>;
};

export default async function MissionDetailPage(props: Props) {
  const { slug } = await props.params;
  return (
    <div className="space-y-4">
      <MissionDetailClient slug={slug} />
    </div>
  );
}
