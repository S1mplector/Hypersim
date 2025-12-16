"""Video and GIF recording for 4D visualizations.

Captures frames from Pygame and exports to various formats.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple, Callable
import os
import tempfile
import shutil

import pygame
import numpy as np


class RecordingFormat(Enum):
    """Supported recording formats."""
    GIF = auto()
    MP4 = auto()
    WEBM = auto()
    PNG_SEQUENCE = auto()


@dataclass
class RecordingConfig:
    """Configuration for recording."""
    fps: int = 30
    width: Optional[int] = None   # None = use screen size
    height: Optional[int] = None
    quality: int = 85  # For lossy formats
    loop: bool = True  # For GIF
    optimize_gif: bool = True


class FrameBuffer:
    """Buffer for storing frames during recording."""
    
    def __init__(self, max_frames: int = 1000):
        self.max_frames = max_frames
        self.frames: List[np.ndarray] = []
        self._temp_dir: Optional[str] = None
        self._frame_count = 0
        self._use_disk = False
    
    def add_frame(self, surface: pygame.Surface) -> None:
        """Add a frame from a Pygame surface."""
        # Convert surface to numpy array
        frame = pygame.surfarray.array3d(surface)
        frame = np.transpose(frame, (1, 0, 2))  # Pygame uses (width, height)
        
        if self._use_disk:
            self._save_frame_to_disk(frame)
        else:
            self.frames.append(frame)
            if len(self.frames) >= self.max_frames:
                self._switch_to_disk()
        
        self._frame_count += 1
    
    def _switch_to_disk(self) -> None:
        """Switch to disk storage when memory limit reached."""
        self._temp_dir = tempfile.mkdtemp(prefix="hypersim_recording_")
        self._use_disk = True
        
        # Save existing frames to disk
        for i, frame in enumerate(self.frames):
            self._save_frame_to_disk(frame, i)
        
        self.frames.clear()
    
    def _save_frame_to_disk(self, frame: np.ndarray, index: Optional[int] = None) -> None:
        """Save a frame to disk."""
        if index is None:
            index = self._frame_count
        
        path = os.path.join(self._temp_dir, f"frame_{index:06d}.npy")
        np.save(path, frame)
    
    def get_frames(self) -> List[np.ndarray]:
        """Get all frames."""
        if self._use_disk:
            frames = []
            for i in range(self._frame_count):
                path = os.path.join(self._temp_dir, f"frame_{i:06d}.npy")
                if os.path.exists(path):
                    frames.append(np.load(path))
            return frames
        return self.frames
    
    def clear(self) -> None:
        """Clear all frames."""
        self.frames.clear()
        self._frame_count = 0
        
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None
            self._use_disk = False
    
    @property
    def frame_count(self) -> int:
        return self._frame_count
    
    def __del__(self):
        self.clear()


class Recorder:
    """Records Pygame frames to video/GIF.
    
    Usage:
        recorder = Recorder()
        recorder.start()
        
        # In render loop:
        recorder.capture_frame(screen)
        
        recorder.stop()
        recorder.save("output.gif")
    """
    
    def __init__(self, config: Optional[RecordingConfig] = None):
        self.config = config or RecordingConfig()
        self.buffer = FrameBuffer()
        self.recording = False
        self._start_time: float = 0
    
    def start(self) -> None:
        """Start recording."""
        self.buffer.clear()
        self.recording = True
        self._start_time = pygame.time.get_ticks() / 1000.0
    
    def stop(self) -> None:
        """Stop recording."""
        self.recording = False
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording
    
    def capture_frame(self, surface: pygame.Surface) -> None:
        """Capture a frame from the given surface."""
        if not self.recording:
            return
        
        # Resize if needed
        if self.config.width and self.config.height:
            if (surface.get_width() != self.config.width or 
                surface.get_height() != self.config.height):
                surface = pygame.transform.scale(
                    surface, (self.config.width, self.config.height)
                )
        
        self.buffer.add_frame(surface)
    
    @property
    def frame_count(self) -> int:
        """Get number of captured frames."""
        return self.buffer.frame_count
    
    @property
    def duration(self) -> float:
        """Get recording duration in seconds."""
        return self.buffer.frame_count / self.config.fps
    
    def save(
        self,
        filename: str,
        format: Optional[RecordingFormat] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Save recording to file.
        
        Args:
            filename: Output filename
            format: Output format (auto-detected from extension if None)
            progress_callback: Called with progress 0-1 during save
            
        Returns:
            True if successful
        """
        if self.buffer.frame_count == 0:
            return False
        
        # Auto-detect format
        if format is None:
            ext = Path(filename).suffix.lower()
            format_map = {
                '.gif': RecordingFormat.GIF,
                '.mp4': RecordingFormat.MP4,
                '.webm': RecordingFormat.WEBM,
                '.png': RecordingFormat.PNG_SEQUENCE,
            }
            format = format_map.get(ext, RecordingFormat.GIF)
        
        frames = self.buffer.get_frames()
        
        if format == RecordingFormat.GIF:
            return self._save_gif(filename, frames, progress_callback)
        elif format == RecordingFormat.MP4:
            return self._save_mp4(filename, frames, progress_callback)
        elif format == RecordingFormat.PNG_SEQUENCE:
            return self._save_png_sequence(filename, frames, progress_callback)
        
        return False
    
    def _save_gif(
        self,
        filename: str,
        frames: List[np.ndarray],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Save as GIF using PIL."""
        try:
            from PIL import Image
        except ImportError:
            print("PIL not available for GIF export. Install with: pip install Pillow")
            return False
        
        images = []
        for i, frame in enumerate(frames):
            img = Image.fromarray(frame.astype('uint8'), 'RGB')
            
            if self.config.optimize_gif:
                img = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
            
            images.append(img)
            
            if progress_callback:
                progress_callback((i + 1) / len(frames) * 0.8)
        
        if images:
            duration = int(1000 / self.config.fps)
            images[0].save(
                filename,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0 if self.config.loop else 1,
                optimize=self.config.optimize_gif,
            )
            
            if progress_callback:
                progress_callback(1.0)
            
            return True
        
        return False
    
    def _save_mp4(
        self,
        filename: str,
        frames: List[np.ndarray],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Save as MP4 using imageio/ffmpeg."""
        try:
            import imageio
        except ImportError:
            print("imageio not available for MP4 export. Install with: pip install imageio[ffmpeg]")
            return False
        
        try:
            writer = imageio.get_writer(
                filename,
                fps=self.config.fps,
                quality=self.config.quality / 10,  # imageio uses 0-10
            )
            
            for i, frame in enumerate(frames):
                writer.append_data(frame)
                if progress_callback:
                    progress_callback((i + 1) / len(frames))
            
            writer.close()
            return True
            
        except Exception as e:
            print(f"MP4 export failed: {e}")
            return False
    
    def _save_png_sequence(
        self,
        filename: str,
        frames: List[np.ndarray],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Save as PNG sequence."""
        try:
            from PIL import Image
        except ImportError:
            print("PIL not available. Install with: pip install Pillow")
            return False
        
        base = Path(filename).stem
        directory = Path(filename).parent
        directory.mkdir(parents=True, exist_ok=True)
        
        for i, frame in enumerate(frames):
            img = Image.fromarray(frame.astype('uint8'), 'RGB')
            img.save(directory / f"{base}_{i:06d}.png")
            
            if progress_callback:
                progress_callback((i + 1) / len(frames))
        
        return True
    
    def clear(self) -> None:
        """Clear recorded frames."""
        self.buffer.clear()


class ScreenshotCapture:
    """Simple screenshot capture utility."""
    
    @staticmethod
    def capture(
        surface: pygame.Surface,
        filename: Optional[str] = None,
        directory: str = ".",
    ) -> str:
        """Capture a screenshot.
        
        Args:
            surface: Pygame surface to capture
            filename: Output filename (auto-generated if None)
            directory: Output directory
            
        Returns:
            Path to saved file
        """
        from datetime import datetime
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hypersim_screenshot_{timestamp}.png"
        
        path = os.path.join(directory, filename)
        pygame.image.save(surface, path)
        
        return path
    
    @staticmethod
    def capture_region(
        surface: pygame.Surface,
        rect: pygame.Rect,
        filename: str,
    ) -> str:
        """Capture a region of the screen."""
        subsurface = surface.subsurface(rect)
        pygame.image.save(subsurface, filename)
        return filename
