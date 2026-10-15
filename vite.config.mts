import { defineConfig } from 'vite';
export default defineConfig({build:{lib:{entry:'frontend/transport.ts',name:'KaikaNetwork',formats:['iife'],fileName:()=> 'transport.js'},outDir:'frontend/dist',emptyOutDir:true}});
