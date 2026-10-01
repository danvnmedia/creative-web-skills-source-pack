> Historical baseline: the showcase was redesigned after visual feedback. For the current files, asset provenance, and 15-case local browser QA, read [Showcase redesign after visual feedback](SHOWCASE-REDESIGN-2026-09-30.md).

# Báo cáo hoàn thiện Harness và Creative Web Skills Pack — 2026-09-30

## Phạm vi và rollback

Đích là repository `D:\Projects\SKILLS\creative-web-skills-source-pack`. Mọi sửa đổi nằm trên branch `codex/harness-skills-motion-20260930`, tách từ commit `a994649`; chưa commit, push, merge hoặc deploy. Có thể xem diff trên branch và quay lại `main` mà không xóa branch. Nguồn Harness v5.5.10 là bản phân phối sibling trong `D:\Projects\IMAGES\black-florest-app-clear-main\Codex_Product_Harness_v5.5.10`.

## Kết quả theo giai đoạn

1. **Cài Harness:** đọc README và hướng dẫn installer, tạo plan 273 thay đổi không xung đột, cài bằng digest đã xác nhận. `WinError 5` ở lần chạy hạn chế được xử lý bằng lần chạy trong ngữ cảnh có quyền. Bootstrap, doctor, self-test, ownership/install verification, skill eval, drift và native verify đã chạy. Xem [installation record](HARNESS-INSTALL-2026-09-30.md).
2. **Audit:** khảo sát cấu trúc repo, sáu skill gốc, bốn showcase, scripts/CI, dependency và các rủi ro về motion/accessibility, truthful copy, tài nguyên ngoài, thiếu command root. Danh sách vấn đề có mức cao/trung/thấp và đề xuất trong [audit](AUDIT-2026-09-30.md).
3. **Nghiên cứu nguồn:** so sánh sáu repo được chọn về mục đích, license, sao và hoạt động quan sát; loại ba repo không phù hợp. Chỉ dùng ý tưởng về ranh giới skill, motion lifecycle, 3D demand rendering và component semantics. Không đưa mã hoặc asset bên thứ ba vào pack. Xem [research table](REPOSITORY-RESEARCH-2026-09-30.md).
4. **Nâng Skills:** thêm `accessible-interaction-systems`, rút gọn trigger của sáu skill hiện có, thêm ghi chú tương thích motion, validator cấu trúc/link và 14 routing review cases. Root có `dev/build/lint/test`, CI có gate skill. Bảy skill qua structural check và security gate với 0 mức block; shader có hai review finding về nội dung network trong tài liệu tham khảo. Xem [skill changelog](SKILLS-CHANGELOG-2026-09-30.md).
5. **Làm lại demo:** Morrow có scroll progress và menu keyboard; Pelagic dùng shader có adaptive resolution, View Transition cho số liệu và copy nêu rõ dữ liệu mô phỏng; Kern dùng spring theo thời gian, rendering on demand, model có khoảng cách/độ tương phản tốt hơn; Asme trở thành travel atlas với ba field note và chuyển ngày/đêm. Mỗi demo ghi ngắn kỹ thuật motion, responsive và reduced-motion behavior. [Browser QA](SHOWCASE-QA-2026-09-30.md) ghi 12/12 trường hợp local qua với ảnh desktop/mobile/reduced motion.

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

Các giới hạn còn lại: chưa đo 60 fps trên thiết bị thật (static auditor còn hai nhắc nhở P2 về scroll listener đã passive và được gom bằng `requestAnimationFrame`); chưa xác nhận GitHub Pages sau deploy; CDN ảnh/font/video/Three có thể không sẵn; static skill validation không chứng minh agent tự kích hoạt đúng skill; `skill-creator` quick validator không chạy vì môi trường Python thiếu PyYAML, trong khi validator của repo và security gate Harness đã chạy. Sau khi review diff và chạy CI, có thể cân nhắc commit/push và kiểm tra Pages trên đúng revision.
