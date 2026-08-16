import { browser } from '$app/environment';

// Svelte 5 reactive state for age confirmation
// Using .svelte.ts extension allows using runes in TS files
export const ageState = $state({
    confirmed: browser ? localStorage.getItem('ageConfirmed') === 'true' : false
});

export function confirmAgeGlobal() {
    if (browser) {
        localStorage.setItem('ageConfirmed', 'true');
        ageState.confirmed = true;
    }
}
