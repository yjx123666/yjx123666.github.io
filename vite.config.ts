import { resolve } from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        software: resolve(__dirname, 'software.html'),
        hobby: resolve(__dirname, 'hobby.html'),
        life: resolve(__dirname, 'life.html'),
        gpsDetail: resolve(__dirname, 'gps-detail.html'),
        gisDetail: resolve(__dirname, 'GIS工具详情.html'),
        mediaDetail: resolve(__dirname, '新媒体工具详情.html'),
      },
    },
    outDir: 'dist',
  },
});
