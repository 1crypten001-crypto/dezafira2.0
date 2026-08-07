// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
  namespace App {
    interface Error {
      message: string;
      code?: string;
    }
    interface Locals {
      user?: {
        id: number;
        username: string;
        role?: string;
        name?: string;
        cpf?: string;
        phone?: string;
      };
      csrfToken?: string;
    }
    interface PageData {}
    interface PageState {}
    interface Platform {}
  }
}

export {};
