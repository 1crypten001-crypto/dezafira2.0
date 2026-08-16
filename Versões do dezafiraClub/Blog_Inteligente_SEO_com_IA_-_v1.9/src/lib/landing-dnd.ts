export type LandingDropPosition = 'before' | 'after' | 'inside';

/** Containers that may directly own content blocks in the visual builder. */
export function acceptsLandingChildren(type: string): boolean {
  // `columns` may only own structural `column` nodes. Letting regular blocks
  // fall directly into it makes them render outside the intended column.
  return type === 'section' || type === 'container' || type === 'column';
}

/** Resolve the same destination shown by the builder's drop indicator. */
export function getLandingDropPosition(
  type: string,
  height: number,
  pointerY: number
): LandingDropPosition {
  const safeHeight = Math.max(1, height);
  const y = Math.min(safeHeight, Math.max(0, pointerY));

  if (acceptsLandingChildren(type)) {
    const edge = Math.min(28, Math.max(12, safeHeight * 0.22));
    if (y < edge) return 'before';
    if (y > safeHeight - edge) return 'after';
    return 'inside';
  }

  return y < safeHeight / 2 ? 'before' : 'after';
}
