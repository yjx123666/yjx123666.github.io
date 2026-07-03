<script setup lang="ts">
import MapComponent from '@/components/MapView.vue'
import ToolBar from '@/components/ToolBar.vue'
import PropertyPanel from '@/components/PropertyPanel.vue'
import LayerPanel from '@/components/LayerPanel.vue'
import SearchPanel from '@/components/SearchPanel.vue'
import MapInfo from '@/components/MapInfo.vue'
</script>

<template>
  <div class="map-view">
    <ToolBar />
    <div class="map-content">
      <MapComponent />
      <SearchPanel />
      <LayerPanel />
      <PropertyPanel />
      <MapInfo />
    </div>
  </div>
</template>

<style scoped>
.map-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}
</style>
