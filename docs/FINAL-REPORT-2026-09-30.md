> The original audit is retained below. For the redesigned demo files and asset provenance, read [Showcase redesign after visual feedback](SHOWCASE-REDESIGN-2026-09-30.md).

# Báo cáo hoàn thiện Harness và Creative Web Skills Pack — 2026-09-30

## Bổ sung sau phản hồi thị giác

Pelagic đã thay trường đường đồng mức bằng ảnh xoáy biển cobalt/turquoise tạo riêng cho repo, kết hợp WebGL khúc xạ và ba trạng thái màu có thể chọn ngay trong hero. Hub cũng dùng đúng ảnh mới. Kern có thêm chương phim quang học 3D bốn giây, dựng từ scene Three.js gốc, xuất MP4 H.264 và poster WebP tự lưu trữ; video chỉ phát khi nằm trong viewport, có nút tạm dừng và đứng yên khi người dùng chọn giảm chuyển động. Cảnh 3D tương tác, Morrow và Asme vẫn hoạt động độc lập.

Bản cập nhật này có source scene, script xuất video, prompt và nguồn gốc asset trong [ghi chép thiết kế](SHOWCASE-REDESIGN-2026-09-30.md). Build, skill lint, repository test và static audit đều chạy; Browser QA local 15/15 ở desktop, mobile và mobile reduced motion, gồm kiểm tra video phát/tạm dừng. Hai P2 scroll-listener cũ còn được auditor ghi nhận; chưa có phép đo 60 fps trên thiết bị vật lý. Phần phát hành live bên dưới mô tả PR #7 trước cập nhật này; revision live của đợt bổ sung cần đối chiếu với `/revision.json` sau khi merge.

## Cập nhật phát hành

- Mã nguồn đã vào `main` qua [PR #7](https://github.com/danvnmedia/creative-web-skills-source-pack/pull/7): commit nguồn `0b62d88464f3a00502fda5c5bacefd9db16916f1`, commit squash trên `main` `3b40c5da13f096a0549683a73ce7ae922774e837`. Commit trước thay đổi là `a994649017853b4f5a11a9ee27819f66112c25b5`; có thể dùng GitHub Revert của PR để rollback.
- [CI trên `main`](https://github.com/danvnmedia/creative-web-skills-source-pack/actions/runs/36804754321) và [workflow Pages](https://github.com/danvnmedia/creative-web-skills-source-pack/actions/runs/36804754384) đều thành công. [Showcase live](https://danvnmedia.github.io/creative-web-skills-source-pack/) và `/revision.json` đã trả đúng commit triển khai `3b40c5d`.
- Playwright Chromium chạy trên URL live: **15/15** trường hợp qua (hub và bốn demo; desktop, mobile, mobile reduced motion); không có page/console error, local HTTP error hoặc local request failure. Chi tiết ở [Browser QA](SHOWCASE-QA-2026-09-30.md). Ảnh và JSON report nằm trong `.ai/evidence/browser/TASK-CREATIVE-001-live-3b40c5d/` ở máy làm việc và được ignore khỏi Git.
- Harness native verify và task validation qua; `evidence_gate.py` cho profile `audited` vẫn mở các điều kiện riêng được nêu cuối báo cáo. Chưa có số đo 60 fps trên thiết bị thật.

## Phạm vi và rollback tại thời điểm audit

Đích là repository `D:\Projects\SKILLS\creative-web-skills-source-pack`. Công việc được thực hiện trên branch `codex/harness-skills-motion-20260930`, tách từ commit `a994649`, rồi merge qua PR #7 như ghi ở trên. Branch làm việc vẫn có cục bộ; GitHub tự xóa nhánh remote sau merge. Nguồn Harness v5.5.10 là bản phân phối sibling trong `D:\Projects\IMAGES\black-florest-app-clear-main\Codex_Product_Harness_v5.5.10`.

## Kết quả theo giai đoạn

1. **Cài Harness:** đọc README và hướng dẫn installer, tạo plan 273 thay đổi không xung đột, cài bằng digest đã xác nhận. `WinError 5` ở lần chạy hạn chế được xử lý bằng lần chạy trong ngữ cảnh có quyền. Bootstrap, doctor, self-test, ownership/install verification, skill eval, drift và native verify đã chạy. Xem [installation record](HARNESS-INSTALL-2026-09-30.md).
2. **Audit:** khảo sát cấu trúc repo, sáu skill gốc, bốn showcase, scripts/CI, dependency và các rủi ro về motion/accessibility, truthful copy, tài nguyên ngoài, thiếu command root. Danh sách vấn đề có mức cao/trung/thấp và đề xuất trong [audit](AUDIT-2026-09-30.md).
3. **Nghiên cứu nguồn:** so sánh sáu repo được chọn về mục đích, license, sao và hoạt động quan sát; loại ba repo không phù hợp. Chỉ dùng ý tưởng về ranh giới skill, motion lifecycle, 3D demand rendering và component semantics. Không đưa mã hoặc asset bên thứ ba vào pack. Xem [research table](REPOSITORY-RESEARCH-2026-09-30.md).
4. **Nâng Skills:** thêm `accessible-interaction-systems`, rút gọn trigger của sáu skill hiện có, thêm ghi chú tương thích motion, validator cấu trúc/link và 14 routing review cases. Root có `dev/build/lint/test`, CI có gate skill. Bảy skill qua structural check và security gate với 0 mức block; shader có hai review finding về nội dung network trong tài liệu tham khảo. Xem [skill changelog](SKILLS-CHANGELOG-2026-09-30.md).
5. **Làm lại demo:** Morrow có scroll progress và menu keyboard; Pelagic dùng shader có adaptive resolution, View Transition cho số liệu và copy nêu rõ dữ liệu mô phỏng; Kern dùng spring theo thời gian, rendering on demand; Asme trở thành travel atlas với ba field note và chuyển ngày/đêm. Sau phản hồi về thẩm mỹ, bốn demo và hub được thiết kế lại theo hướng experimental rõ hơn, dùng ảnh do dự án tạo và lưu tại repo. Mỗi demo ghi ngắn kỹ thuật motion, responsive và reduced-motion behavior. [Browser QA](SHOWCASE-QA-2026-09-30.md) ghi 15/15 trường hợp local và 15/15 trường hợp live qua với ảnh desktop/mobile/reduced motion.

## Repo đã áp dụng

| Nguồn | Đã áp dụng |
|---|---|
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | Ranh giới skill, trigger rõ và kiểm tra cấu trúc/link |
| [motiondivision/motion](https://github.com/motiondivision/motion) | Nguyên tắc spring, scroll-linked motion và reduced motion; demo dùng implementation gốc của repo |
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | Vòng đời WebGL, render khi cần, disposal và poster fallback |
| [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) | Ý tưởng demand rendering trong hướng dẫn 3D; demo vanilla không nhập R3F |
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Semantics, trạng thái focus/keyboard và component contract, không sao chép giao diện |
| [greensock/GSAP](https://github.com/greensock/GSAP) | Chỉ tham khảo kiến trúc timeline/cleanup; không thêm package hoặc mã GSAP |

License và lý do loại được ghi cụ thể trong [research table](REPOSITORY-RESEARCH-2026-09-30.md).

## Danh sách thay đổi

- **Harness và metadata:** `.ai/`, `.agents/`, `AGENTS.md`, `ANTIGRAVITY.md`, `CLAUDE.md`, `GEMINI.md`, `.gitattributes`.
- **Skills:** sáu `*/SKILL.md` hiện có; `accessible-interaction-systems/` (entrypoint, agent metadata, references); `motion-choreographer/references/modern-motion-support.md`.
- **Repo và kiểm tra:** `package.json`, `package-lock.json`, `.gitignore`, `.github/workflows/ci.yml`, `scripts/build-pages-site.mjs`, `scripts/validate-repository.mjs`, `scripts/validate-skills.mjs`, `scripts/skill-routing-cases.json`, `scripts/serve-showcase.mjs`, `scripts/qa-showcases.mjs`.
- **Demos và portal:** `showcase-sites/index.html`, `showcase-sites/README.md`, ba bộ `index.html`/`style.css`/`app.js` dưới `morrow-archive/`, `pelagic-signals/`, `kern-one/`; `showcase-apps/asme-hero/src/App.tsx` và `index.css`; `README.md`, `SHOWCASE-INDEX.md`.
- **Báo cáo:** `docs/HARNESS-INSTALL-2026-09-30.md`, `AUDIT-2026-09-30.md`, `REPOSITORY-RESEARCH-2026-09-30.md`, `SKILLS-CHANGELOG-2026-09-30.md`, `SHOWCASE-QA-2026-09-30.md`, và file này.

## Open-source hygiene và việc còn lại

`.gitignore` loại `.env*` (trừ example), private key, dependency/build/cache, generated Asme/Pages, và các checkpoint/event/log/browser/completion artifacts do Harness sinh ra vì chúng chứa đường dẫn máy cục bộ và chỉ có giá trị runtime. Source Harness, ownership state, task contract và các báo cáo review vẫn hiện trong Git để người duy trì xem xét. Không có credential nào được đưa vào browser bundle theo kiểm tra mã nguồn và runtime hiện tại; vẫn nên chạy secret scanning trong PR trước khi công khai branch.

**Trạng thái gate Harness:** `harness.py verify --profile native` PASS trên bản cài, và bằng chứng task cho build, browser, critical flow, external probe, performance, security, skill-eval contract, skill-security contract và surface drift đã được ghi. `evidence_gate.py` của task vẫn FAIL vì profile `audited` yêu cầu nhiều regression contract của distribution nguồn cùng `skill-eval-live`. Lần thử audited trong repo đích cho thấy các regression nguồn không có distribution marker và một số test tạo thư mục ở Windows Temp bị `WinError 5`; không đổi code hay đánh dấu waiver để che lỗi. Task Harness giữ `IN_PROGRESS` cho đến khi các gate đó có bằng chứng thích hợp hoặc phạm vi task được chuẩn hóa ở distribution nguồn.

Các giới hạn còn lại: chưa đo 60 fps trên thiết bị thật (static auditor còn hai nhắc nhở P2 về scroll listener đã passive và được gom bằng `requestAnimationFrame`); một số font/video/Three CDN vẫn có thể không sẵn; static skill validation không chứng minh agent tự kích hoạt đúng skill; `skill-creator` quick validator không chạy vì môi trường Python thiếu PyYAML, trong khi validator của repo và security gate Harness đã chạy. GitHub Pages đã được kiểm tra trên đúng revision như phần cập nhật phát hành.
