import { writable } from 'svelte/store';

export const simState = writable({
    pos:  [0, 0, 0],
    quat: [1, 0, 0, 0],
});