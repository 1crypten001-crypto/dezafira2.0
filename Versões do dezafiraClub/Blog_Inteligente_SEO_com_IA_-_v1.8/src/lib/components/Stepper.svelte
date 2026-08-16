<script lang="ts">
  let { 
    step = 1,
    steps = [],
    current = 1,
    variant = 'default',
    direction = 'horizontal',
    clickable = false
  } = $props();

  let totalSteps = $derived(steps.length || step);

  function isCompleted(index: number): boolean {
    return index + 1 < current;
  }

  function isCurrent(index: number): boolean {
    return index + 1 === current;
  }

  function isUpcoming(index: number): boolean {
    return index + 1 > current;
  }

  function goToStep(index: number) {
    if (clickable && index + 1 < current) {
      // Allow going back
      current = index + 1;
    }
  }
</script>

<div class="stepper variant-{variant} direction-{direction}">
  {#each Array(totalSteps) as _, index}
    <div 
      class="step"
      class:completed={isCompleted(index)}
      class:current={isCurrent(index)}
      class:upcoming={isUpcoming(index)}
      class:clickable
      onclick={() => goToStep(index)}
      onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && goToStep(index)}
      role="button"
      tabindex={clickable ? 0 : -1}
      aria-label="Passo {index + 1}"
    >
      <div class="step-indicator">
        {#if isCompleted(index)}
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
          </svg>
        {:else}
          <span class="step-number">{index + 1}</span>
        {/if}
      </div>

      {#if variant !== 'compact' && steps[index]}
        <div class="step-content">
          <span class="step-label">{steps[index].label}</span>
          {#if steps[index].description}
            <span class="step-description">{steps[index].description}</span>
          {/if}
        </div>
      {/if}

      {#if index < totalSteps - 1}
        <div class="step-connector" class:completed={isCompleted(index)}></div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .stepper {
    width: 100%;
    display: flex;
    align-items: flex-start;
    gap: 0;
  }

  /* Direction */
  .direction-vertical {
    flex-direction: column;
  }

  .step {
    display: flex;
    align-items: flex-start;
    flex: 1;
    position: relative;
  }

  .direction-vertical .step {
    flex-direction: row;
    flex: none;
    align-items: center;
    min-height: 60px;
  }

  .step.clickable {
    cursor: pointer;
  }

  /* Indicator */
  .step-indicator {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #e5e7eb;
    color: #9ca3af;
    font-weight: 600;
    font-size: 14px;
    flex-shrink: 0;
    transition: all 0.2s;
  }

  .step.current .step-indicator {
    background: #4a90d9;
    color: white;
    box-shadow: 0 0 0 4px rgba(74, 144, 217, 0.2);
  }

  .step.completed .step-indicator {
    background: #10b981;
    color: white;
  }

  .step.completed:hover .step-indicator {
    transform: scale(1.05);
  }

  .step-indicator svg {
    width: 18px;
    height: 18px;
  }

  .step-number {
    line-height: 1;
  }

  /* Content */
  .step-content {
    padding-left: 12px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .direction-vertical .step-content {
    padding-left: 16px;
    flex: 1;
  }

  .step-label {
    font-size: 14px;
    font-weight: 500;
    color: #9ca3af;
  }

  .step.current .step-label {
    color: #1f2937;
  }

  .step.completed .step-label {
    color: #374151;
  }

  .step-description {
    font-size: 12px;
    color: #9ca3af;
  }

  /* Connector */
  .step-connector {
    flex: 1;
    height: 2px;
    background: #e5e7eb;
    margin: 17px 8px 0;
    position: relative;
  }

  .direction-vertical .step-connector {
    width: 2px;
    height: auto;
    min-height: 40px;
    margin: 0;
    position: absolute;
    left: 18px;
    top: 36px;
  }

  .step-connector.completed {
    background: #10b981;
  }

  /* Compact variant */
  .variant-compact .step-indicator {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .variant-compact .step-connector {
    margin-top: 14px;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .step-content {
      display: none;
    }

    .stepper {
      justify-content: center;
    }

    .step {
      flex: none;
    }

    .step-connector {
      width: 40px;
      margin: 0 4px;
      flex: none;
    }

    .direction-vertical .step-content {
      display: flex;
    }

    .direction-vertical .step-connector {
      display: none;
    }
  }
</style>