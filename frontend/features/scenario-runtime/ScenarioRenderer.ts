import type { ScenarioRuntimeState } from "./types";

type RuntimePalette = {
  base: string;
  glow: string;
  horizon: string;
};

const MODE_PALETTES: Record<ScenarioRuntimeState["runtimeMode"], RuntimePalette> = {
  tool: {
    base: "#0f1d3a",
    glow: "#2dd4bf",
    horizon: "#0ea5e9",
  },
  game: {
    base: "#240f05",
    glow: "#f97316",
    horizon: "#f59e0b",
  },
  ai: {
    base: "#061a1a",
    glow: "#22d3ee",
    horizon: "#14b8a6",
  },
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export class ScenarioRenderer {
  private canvas: HTMLCanvasElement | null = null;
  private context: CanvasRenderingContext2D | null = null;

  attach(canvas: HTMLCanvasElement): void {
    const context = canvas.getContext("2d", { alpha: false });
    if (!context) {
      return;
    }
    this.canvas = canvas;
    this.context = context;
  }

  detach(): void {
    this.canvas = null;
    this.context = null;
  }

  render(state: ScenarioRuntimeState, timestamp: number): void {
    if (!this.canvas || !this.context) {
      return;
    }

    const rect = this.canvas.getBoundingClientRect();
    const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    const targetWidth = Math.max(1, Math.floor(rect.width * dpr));
    const targetHeight = Math.max(1, Math.floor(rect.height * dpr));

    if (this.canvas.width !== targetWidth || this.canvas.height !== targetHeight) {
      this.canvas.width = targetWidth;
      this.canvas.height = targetHeight;
    }

    const ctx = this.context;
    const stageWidth = state.stage.width;
    const stageHeight = state.stage.height;
    const scaleX = targetWidth / stageWidth;
    const scaleY = targetHeight / stageHeight;

    ctx.setTransform(scaleX, 0, 0, scaleY, 0, 0);
    ctx.imageSmoothingEnabled = true;

    const palette = MODE_PALETTES[state.runtimeMode];
    const gradient = ctx.createLinearGradient(0, 0, stageWidth, stageHeight);
    gradient.addColorStop(0, palette.base);
    gradient.addColorStop(1, "#020617");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, stageWidth, stageHeight);

    const ambient = ctx.createRadialGradient(
      state.pointer.x,
      state.pointer.y,
      24,
      state.pointer.x,
      state.pointer.y,
      stageWidth * 0.48,
    );
    ambient.addColorStop(0, `${palette.glow}44`);
    ambient.addColorStop(1, "#00000000");
    ctx.fillStyle = ambient;
    ctx.fillRect(0, 0, stageWidth, stageHeight);

    this.drawGrid(ctx, stageWidth, stageHeight, palette);

    for (const entity of state.entities) {
      const pulse = Math.sin(timestamp * 0.003 + entity.energy * 3.7);
      const radius = entity.radius * (1 + pulse * 0.08 + (entity.highlighted ? 0.16 : 0));
      const alpha = clamp(0.28 + entity.energy * 0.36, 0.18, 0.85);

      const glowGradient = ctx.createRadialGradient(entity.x, entity.y, radius * 0.28, entity.x, entity.y, radius * 2.2);
      glowGradient.addColorStop(0, `hsla(${entity.hue} 94% 63% / ${alpha})`);
      glowGradient.addColorStop(1, "rgba(0, 0, 0, 0)");

      ctx.fillStyle = glowGradient;
      ctx.beginPath();
      ctx.arc(entity.x, entity.y, radius * 2.2, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = `hsla(${entity.hue} 100% 72% / ${clamp(alpha + 0.2, 0.28, 0.96)})`;
      ctx.beginPath();
      ctx.arc(entity.x, entity.y, radius, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = `hsla(${entity.hue} 100% 90% / ${clamp(alpha + 0.24, 0.3, 1)})`;
      ctx.lineWidth = entity.highlighted ? 2.6 : 1.4;
      ctx.beginPath();
      ctx.arc(entity.x, entity.y, radius + 1.3, 0, Math.PI * 2);
      ctx.stroke();
    }

    this.drawHud(ctx, state, palette);
  }

  private drawGrid(
    ctx: CanvasRenderingContext2D,
    stageWidth: number,
    stageHeight: number,
    palette: RuntimePalette,
  ): void {
    const step = 72;
    ctx.strokeStyle = `${palette.horizon}22`;
    ctx.lineWidth = 1;
    for (let x = 0; x <= stageWidth; x += step) {
      ctx.beginPath();
      ctx.moveTo(x + 0.5, 0);
      ctx.lineTo(x + 0.5, stageHeight);
      ctx.stroke();
    }
    for (let y = 0; y <= stageHeight; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y + 0.5);
      ctx.lineTo(stageWidth, y + 0.5);
      ctx.stroke();
    }
  }

  private drawHud(
    ctx: CanvasRenderingContext2D,
    state: ScenarioRuntimeState,
    palette: RuntimePalette,
  ): void {
    const width = 360;
    const height = 96;
    const x = state.stage.width - width - 24;
    const y = 22;

    ctx.fillStyle = "rgba(2, 6, 23, 0.52)";
    ctx.fillRect(x, y, width, height);
    ctx.strokeStyle = `${palette.horizon}66`;
    ctx.lineWidth = 1.2;
    ctx.strokeRect(x, y, width, height);

    ctx.fillStyle = "rgba(236, 253, 245, 0.92)";
    ctx.font = "600 16px var(--font-sans)";
    ctx.fillText(`Mode: ${state.runtimeMode.toUpperCase()}  |  Tier: ${state.tier.toUpperCase()}`, x + 16, y + 30);

    ctx.fillStyle = "rgba(226, 232, 240, 0.92)";
    ctx.font = "500 13px var(--font-mono)";
    ctx.fillText(`FPS ${state.metrics.fps}  REACTION ${state.metrics.reactionMs}ms`, x + 16, y + 54);
    ctx.fillText(`INTERACTIONS ${state.metrics.interactions}  SCORE ${Math.round(state.metrics.score)}`, x + 16, y + 74);
  }
}
