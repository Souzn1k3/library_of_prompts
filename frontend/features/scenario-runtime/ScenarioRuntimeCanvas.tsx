"use client";

import { useEffect, useRef } from "react";

import { InteractionController } from "./InteractionController";
import { ScenarioRenderer } from "./ScenarioRenderer";
import { ScenarioRuntimeEngine } from "./ScenarioRuntimeEngine";

type ScenarioRuntimeCanvasProps = {
  engine: ScenarioRuntimeEngine;
  controller: InteractionController;
  stageWidth: number;
  stageHeight: number;
  className?: string;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function mapPoint(
  element: HTMLElement,
  clientX: number,
  clientY: number,
  stageWidth: number,
  stageHeight: number,
): { x: number; y: number } {
  const rect = element.getBoundingClientRect();
  const x = ((clientX - rect.left) / Math.max(1, rect.width)) * stageWidth;
  const y = ((clientY - rect.top) / Math.max(1, rect.height)) * stageHeight;

  return {
    x: clamp(x, 0, stageWidth),
    y: clamp(y, 0, stageHeight),
  };
}

export function ScenarioRuntimeCanvas({
  engine,
  controller,
  stageWidth,
  stageHeight,
  className,
}: ScenarioRuntimeCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const renderer = new ScenarioRenderer();
    renderer.attach(canvas);
    engine.attachRenderer(renderer);

    return () => {
      engine.detachRenderer(renderer);
      renderer.detach();
    };
  }, [engine]);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      onPointerMove={(event) => {
        const point = mapPoint(event.currentTarget, event.clientX, event.clientY, stageWidth, stageHeight);
        controller.hover(point.x, point.y);
      }}
      onPointerDown={(event) => {
        const point = mapPoint(event.currentTarget, event.clientX, event.clientY, stageWidth, stageHeight);
        controller.click(point.x, point.y);
      }}
      onTouchStart={(event) => {
        const touch = event.touches[0];
        if (!touch) {
          return;
        }
        const point = mapPoint(event.currentTarget, touch.clientX, touch.clientY, stageWidth, stageHeight);
        controller.touch(point.x, point.y);
      }}
      onTouchMove={(event) => {
        const touch = event.touches[0];
        if (!touch) {
          return;
        }
        const point = mapPoint(event.currentTarget, touch.clientX, touch.clientY, stageWidth, stageHeight);
        controller.hover(point.x, point.y);
      }}
      aria-label="Scenario runtime interactive stage"
      role="img"
    />
  );
}
