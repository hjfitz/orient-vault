#interview #bifrost 
## Schuster
- overall thought it was great structure
- showcased his abilities very well
- why did he hand-roll a csv parser with the time limit?
- his use of typescript:
	- interesting use of inlining types & there's a lot of inference
	- good naming all round
- great separation of concerns in his codebase and good architecture
- there was an interesting use of map - using it twice
- overall thought it was very high quality


---

## Harry

- enjoyed the field mapping. approach scales very well and almost mirrors our approach within our primary aim
- not bad - very funtional. our team writes very OOP heavy typescript 
- there was a lot of tight coupling in the codebase
	- would like to see the core logic moved from the controller layer
	- controller should read like a story
	- makes it difficult to scale
	- were some magic strings and numbers (eg, when doing the kg/lb conversion)
	- overall not an issue due to where he's positioned as a developer
- lots of use of any
- overall clever pattern and works very well

---

# refined

## **Schuster**

**Overall Impression**

- Strong performance with excellent structure and clarity.
    
- Delivered a high-quality submission that showcased his abilities very well.
    

**Strengths**

- Very clean architecture with good separation of concerns.
    
- Effective use of TypeScript, including naming and inferred/inlined types.
    
- Code felt polished and thoughtfully organised.
    

**Areas to Explore / Questions**

- He hand-rolled a CSV parser despite the time limit — curious decision and worth discussing.
    
- Minor curiosity around using `map` twice in one of the implementations (not incorrect, just interesting).
    

**Summary**

- High-quality submission, technically strong, and well put together.
    

---

## **Harry**

**Overall Impression**

- Solid submission with a clever and scalable field-mapping approach.
    
- The mapping logic mirrors patterns used in our own production system, which is a strong positive.
    

**Strengths**

- Functional approach worked well and showed good problem-solving.
    
- Demonstrated strong intuition around extensible mappings.
    

**Areas for Development**

- Codebase showed tight coupling:
    
    - Would benefit from moving core logic out of the controller layer.
        
    - Controllers should read more narratively (“like a story”).
        
    - Current structure may limit scalability.
        
- Some reliance on magic strings/numbers (e.g., kg/lb conversion).
    
- Heavy use of `any`, which weakens type safety.
    
- OOP usage is limited compared to how the team typically writes TypeScript, but this aligns with his current level.
    

**Summary**

- Thoughtful solution with a strong underlying pattern.
    
- Some structural refinements would elevate the maintainability and scalability.