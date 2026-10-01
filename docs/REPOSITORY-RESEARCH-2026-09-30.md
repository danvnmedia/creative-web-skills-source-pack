# Chắt lọc repository — ảnh chụp 2026-09-30

Số sao và ngày hoạt động là ảnh chụp GitHub tại thời điểm nghiên cứu, có thể đổi. "Cập nhật" là ngày GitHub hiển thị hoặc ngày commit mới nhất quan sát được, không phải cam kết về chu kỳ phát hành. Chỉ học pattern và cấu trúc; không nhập mã, media, prompt hay ví dụ của bên thứ ba.

| Repo | Mục đích | License | Phổ biến | Cập nhật quan sát | Điểm đáng học và mức phù hợp |
|---|---|---|---:|---|---|
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | Workflow và chất lượng agent skills | MIT | ~100.1k sao | [2026-09-26](https://github.com/addyosmani/agent-skills/commits) | Kiểm tra cấu trúc, link tham khảo và ranh giới giữa các skill; áp dụng validator có bằng chứng. **5/5** |
| [motiondivision/motion](https://github.com/motiondivision/motion) | Motion cho JS/React, spring, gesture, scroll | MIT | ~33.8k sao | [2026-09-30](https://github.com/motiondivision) | Chọn spring cho phản hồi trực tiếp và scroll-linked khi có ý nghĩa; giữ engine ownership rõ. **5/5** |
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | Nền tảng 3D WebGL/WebGPU | MIT | ~115k sao | [ít nhất 2026-09-21](https://github.com/mrdoob/three.js/commits) | Xử lý vòng đời renderer, giải phóng tài nguyên, fallback tĩnh; không nâng version demo chỉ vì bản mới. **5/5** |
| [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) | React renderer cho Three.js | MIT | ~32.6k sao | [2026-09-16](https://github.com/orgs/pmndrs/repositories) | Demand-driven render và ranh giới React/scene; đưa vào hướng dẫn 3D, không thêm R3F vào demo vanilla. **4/5** |
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Component có thể ghép, thiết kế accessible | MIT | ~124.9k sao | [2026-09-29](https://github.com/shadcn-ui) | Semantics, trạng thái focus/keyboard và token thống nhất; không sao chép thẩm mỹ mặc định. **4/5** |
| [greensock/GSAP](https://github.com/greensock/GSAP) | Timeline, ScrollTrigger, FLIP | [Standard no-charge](https://gsap.com/standard-license/) (không phải MIT) | ~28.7k sao | [2026-04-13](https://github.com/greensock) | Học ranh giới timeline và cleanup cho cảnh phức tạp; chỉ tham khảo tài liệu, không nhập mã/dependency cho bốn demo hiện tại. **4/5** |

## Đã loại khỏi nguồn áp dụng

- [anthropics/skills](https://github.com/anthropics/skills): repo rất phổ biến và còn hoạt động, nhưng license theo từng skill; ví dụ [xlsx](https://github.com/anthropics/skills/blob/main/skills/xlsx/LICENSE.txt) có giới hạn sao chép/phái sinh. Không dùng làm nguồn mã hoặc văn bản cho pack MIT này.
- [motiondivision/motionone](https://github.com/motiondivision/motionone): GitHub đánh dấu archived, cập nhật cuối 2024-11-12; dùng Motion hiện hành.
- [JosephASG/codrops-cinematic-scroll-animations](https://github.com/JosephASG/codrops-cinematic-scroll-animations): demo tutorial hẹp (81 sao, 12 commit), hữu ích để tham khảo hiệu ứng nhưng không đủ mạnh làm nền kiến trúc/skill lâu dài.
- Đã bỏ hai link repo cũ thiếu bằng chứng license hoặc maintenance khỏi `SHOWCASE-INDEX.md`; bảng này là nguồn chắt lọc chính cho đợt nâng cấp.

## Áp dụng vào dự án

1. Giữ sáu skill chuyên biệt và thêm skill thứ bảy cho component accessible; rút frontmatter thành trigger phân biệt được. Validator kiểm tra frontmatter, metadata, link tương đối, và ma trận định tuyến tĩnh.
2. Dùng cùng một hợp đồng motion: trigger, trạng thái đầu/cuối, cleanup, reduced motion, mobile, và bằng chứng trình duyệt. Cập nhật ví dụ theo các kỹ thuật đó, không đưa code từ repo tham khảo vào.
3. Dùng CSS scroll timeline sau `@supports`, fallback nội dung tĩnh hoặc IntersectionObserver; View Transitions là enhancement có kiểm tra hỗ trợ; spring dành cho tương tác trực tiếp. [MDN cho biết scroll timelines chưa Baseline rộng](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-timeline/scroll), còn [same-document View Transitions là Baseline 2025 trên trình duyệt mới](https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition) và [reduced motion đã phổ biến từ 2020](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion).
4. Nâng cấp bốn showcase theo bốn ngôn ngữ thị giác riêng; Asme được làm lại thành travel atlas. Dùng transform/opacity cho chuyển động liên tục, giới hạn việc đọc layout, giữ nội dung và keyboard flow khi hiệu ứng bị tắt.
