# Vertical frame rate and export recommendation

Checked 17 October 2026, Europe/Stockholm. User asked for higher frame rate and clearer imagery after the initial landscape version. Recommended delivery: a newly rendered **1080×1920, 120 fps local master** and a **1080×1920, 60 fps TikTok upload copy**, both 20 seconds and using the original synthesized score.

## Official finding and exact scope

The official [TikTok Developers Media Transfer Guide](https://developers.tiktok.com/docs/en/content-posting-api-media-transfer-guide?enter_method=left_navigation), labelled updated 4 August 2026 and opened during this check, specifies **23–60 fps for media transferred through the Content Posting API**. It recommends MP4 and H.264, lists 360–4096px for each image dimension and a 4GB maximum. The API documentation directly supports a 60 fps upload copy; it does not establish every mobile-app organic upload or playback limit.

No current official confirmation of 120 fps organic app upload/playback was found. Do not tell the user that TikTok will preserve or display the 120 fps master. Describe it as the local high-frame-rate master; describe the 60 fps file as the TikTok upload copy. The paid ad page's limits must not be presented as organic frame-rate limits.

The official [TikTok Auction In-Feed Ads guidance](https://ads.tiktok.com/resources/help/article/tiktok-auction-in-feed-ads?lang=en), updated June 2026, still supports vertical 9:16 and variable placement safe zones. It does not make the chosen x90–900/y240–1480 house inset a universal official rectangle. Actual phone/upload previews remain required before publishing.

## Export metadata and verification

| Property | Local master | TikTok upload copy |
|---|---|---|
| Frame dimensions | 1080×1920 | 1080×1920 |
| Display / pixel geometry | 9:16 display, 1:1 sample aspect, no rotation metadata | Same |
| Video frame rate | Constant 120/1 | Constant 60/1 |
| Video frame count at 20s | 2400 | 1200 |
| Video format | MP4; H.264 High profile with an encoder-selected valid level | MP4; H.264 High profile with an encoder-selected valid level |
| Pixel format | yuv420p for broad MP4 playback | yuv420p |
| Quality starting point | CRF around 14–16 with a suitable quality preset; inspect rather than relying on a bitrate alone | High-quality downsample from native render, CRF around 15–17; avoid repeated lossy encodes |
| Colour | Correct RGB→YUV conversion with consistent BT.709 tags/range; inspect gradients and black level | Same |
| Audio | Original stereo score, AAC at 48kHz, approximately 256–320kbps | Same |
| MP4 layout | Faststart / moov atom before media | Same |

These are production recommendations, not claimed TikTok mandates. Do not force an incompatible H.264 level merely to match a label. Let the encoder choose a valid level for the actual frame geometry/rate and verify the result with ffprobe.

The master must sample the animation at **t=i/120** for all 2400 frames. Doubling a 60 fps file or using a 120 fps container tag does not create newly sampled motion. Generate the 60 fps copy by selecting alternate native frames (or an equivalent deterministic 60 fps render), without interpolating across the genuine screenshot states. A stationary reading hold may legitimately contain repeated frames; inspect an actively transforming segment to confirm the native intermediate motion exists.

Verify ffprobe reports width/height, SAR/DAR, r_frame_rate and avg_frame_rate, codec/pixel format, audio sample rate/channel count and duration. Fully decode both outputs and check final video frame counts. Inspect type, screenshot query/result, contours, thin lines and gradients after encoding. Check no accidental black/blank frames, transition discontinuity or audio clipping/truncated tail. The 120 fps master needs compatible playback hardware/software; that is a viewing constraint, not a reason to mislabel a 60 fps duplicate.

## Clarity is also a design task

Use the new native portrait composition, natural font proportions and a stable enlarged product crop. Keep essential copy, query/result and CTA inside x90–900/y240–1480. Higher fps improves temporal sampling, while readable type, held results and correct pixel geometry address the user's clarity complaint. Retain the input/result stationary; the surrounding contour may transform before and after the proof.

Fresh captures independently inspected: `vertical-captures/directory-09.png`, `capture-note.txt`, and `manifest.json`. The logged-out Microsoft interaction was recaptured at 15:43 Europe/Stockholm on 17 October 2026. The genuine final image shows a role-count display that remains unverified against an employer source. Keep source header counts and the card's number outside the creative crop as planned. A consistent source crop ending by approximately y830 preserves the query/name/description without promoting that availability number.

**Status:** export plan supported; actual vertical storyboard/master/upload copy still require inspection. No publication or source edits performed by this reviewer.
