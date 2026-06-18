import { Navbar } from "../components/landing/Navbar";
import { Hero } from "../components/landing/Hero";
import { ProblemSolution } from "../components/landing/ProblemSolution";
import { FeatureCards } from "../components/landing/FeatureCards";
import { ArchitectureFlow } from "../components/landing/ArchitectureFlow";
import { DemoScenario } from "../components/landing/DemoScenario";
import { EvaluationPreview } from "../components/landing/EvaluationPreview";
import { Compliance } from "../components/landing/Compliance";
import { Footer } from "../components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Hero />
        <ProblemSolution />
        <FeatureCards />
        <ArchitectureFlow />
        <DemoScenario />
        <EvaluationPreview />
        <Compliance />
      </main>
      <Footer />
    </div>
  );
}
