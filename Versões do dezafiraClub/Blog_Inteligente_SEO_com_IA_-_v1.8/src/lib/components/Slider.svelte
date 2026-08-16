<script lang="ts">
  let { 
    min = 0,
    max = 100,
    value = 50,
    step = 1,
    disabled = false,
    label = '',
    showValue = true,
    showMinMax = false,
    variant = 'default',
    orientation = 'horizontal',
    size = 'md'
  } = $props();

  let dragging = $state(false);

  let percent = $derived(((value - min) / (max - min)) * 100);
  let trackFill = $derived(`${percent}%`);
  let trackEmpty = $derived(`${100 - percent}%`);

  function handleInput(e: Event) {
    const target = e.target as HTMLInputElement;
    value = parseFloat(target.value);
  }

  function getSizeValue(): string {
    switch (size) {
      case 'sm': return '4px';
      case 'md': return '8px';
      case 'lg': return '12px';
      default: return '8px';
    }
  }

  let thumbSize = $derived(getSizeValue());
</script>

<div class="slider-container variant-{variant} orientation-{orientation} size-{size}" class:disabled>
  {#if label}
    <label class="slider-label" for="slider-input">{label}</label>
  {/if}

  <div class="slider-wrapper">
    {#if showMinMax}
      <span class="slider-min">{min}</span>
    {/if}

    <div class="slider-track">
      <div 
        class="slider-fill" 
        style="width: {trackFill}"
      ></div>

      <input
        type="range"
        id="slider-input"
        {min}
        {max}
        {step}
        bind:value
        oninput={handleInput}
        {disabled}
        class="slider-input"
        aria-label={label || 'Slider'}
      />
    </div>

    {#if showMinMax}
      <span class="slider-max">{max}</span>
    {/if}

    {#if showValue}
      <span class="slider-value">{value}</span>
    {/if}
  </div>
</div>

<style>
  .slider-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .slider-container.disabled {
    opacity: 0.5;
    pointer-events: none;
  }

  .slider-label {
    font-size: 14px;
    font-weight: 500;
    color: #374151;
  }

  .slider-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .orientation-vertical .slider-wrapper {
    flex-direction: column-reverse;
    height: 200px;
  }

  .slider-min,
  .slider-max {
    font-size: 12px;
    color: #9ca3af;
    min-width: 30px;
  }

  .slider-min {
    text-align: right;
  }

  .slider-value {
    font-size: 14px;
    font-weight: 600;
    color: #4a90d9;
    min-width: 40px;
    text-align: center;
  }

  .slider-track {
    flex: 1;
    position: relative;
    height: 24px;
    display: flex;
    align-items: center;
  }

  .orientation-vertical .slider-track {
    width: 24px;
    height: 100%;
    flex-direction: column;
  }

  .slider-fill {
    position: absolute;
    background: linear-gradient(90deg, #4a90d9, #67b26f);
    border-radius: 100px;
    pointer-events: none;
    transition: width 0.1s, height 0.1s;
  }

  .orientation-horizontal .slider-fill {
    height: var(--track-height, 6px);
    left: 0;
  }

  .orientation-vertical .slider-fill {
    width: var(--track-height, 6px);
    bottom: 0;
    left: auto;
    background: linear-gradient(0deg, #4a90d9, #67b26f);
  }

  .slider-input {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 24px;
    background: transparent;
    cursor: pointer;
    position: relative;
    z-index: 1;
  }

  .orientation-vertical .slider-input {
    writing-mode: vertical-lr;
    direction: rtl;
    width: 24px;
    height: 100%;
  }

  /* Thumb - Webkit */
  .slider-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: var(--thumb-size, 20px);
    height: var(--thumb-size, 20px);
    border-radius: 50%;
    background: white;
    border: 3px solid #4a90d9;
    cursor: grab;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }

  .slider-input::-webkit-slider-thumb:hover {
    transform: scale(1.1);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
  }

  .slider-input::-webkit-slider-thumb:active {
    cursor: grabbing;
    transform: scale(1.15);
  }

  /* Thumb - Firefox */
  .slider-input::-moz-range-thumb {
    width: var(--thumb-size, 20px);
    height: var(--thumb-size, 20px);
    border-radius: 50%;
    background: white;
    border: 3px solid #4a90d9;
    cursor: grab;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }

  /* Track - Webkit */
  .slider-input::-webkit-slider-runnable-track {
    height: 6px;
    background: #e5e7eb;
    border-radius: 100px;
  }

  .orientation-vertical .slider-input::-webkit-slider-runnable-track {
    width: 6px;
    height: 100%;
  }

  /* Sizes */
  :global(.size-sm) {
    --track-height: 4px;
    --thumb-size: 16px;
  }

  :global(.size-md) {
    --track-height: 6px;
    --thumb-size: 20px;
  }

  :global(.size-lg) {
    --track-height: 10px;
    --thumb-size: 28px;
  }
</style>