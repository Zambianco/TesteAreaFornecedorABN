window.onload = function(){
    document.querySelector('body .loader').remove();

    $('.banners .owl-carousel').owlCarousel({
        margin: 0,
        loop: true,
        dots: true,
        nav: true,
        navText: ['<svg width="14" height="25" viewBox="0 0 14 25" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M0.556645 13.8887L11.3117 25L14 22.2227L4.58908 12.5L14 2.77734L11.3117 0L0.556645 11.1113C0.200225 11.4797 -5.13324e-08 11.9792 -5.13324e-08 12.5C-5.13324e-08 13.0208 0.200225 13.5203 0.556645 13.8887Z" fill="white"/></svg>','<svg width="14" height="25" viewBox="0 0 14 25" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M13.4434 13.8887L2.68829 25L0 22.2227L9.41092 12.5L0 2.77734L2.68829 0L13.4434 11.1113C13.7998 11.4797 14 11.9792 14 12.5C14 13.0208 13.7998 13.5203 13.4434 13.8887Z" fill="white"/></svg>'],
        lazyLoad: true,
        autoplay: true,
        autoplayTimeout: 9000,
        items: 1,
        autoHeight: true
    });

    let allItens = 0;
    document.querySelectorAll('.banners .owl-carousel .owl-stage>*:not(.cloned)').forEach(item=>{allItens++});

    document.querySelectorAll('.banners .owl-carousel .owl-dots>*:not(.cloned)').forEach((dot,index)=>{
        dot.innerHTML = `<strong>${index+1<=9 ? `0${index+1}` : index+1}</strong> /${allItens<=9 ? `0${allItens}` : allItens}`;
    });

    $('.solucoes .owl-carousel').owlCarousel({
        margin: 15,
        rewind: true,
        dots: false,
        nav: false,
        lazyLoad: true,
        autoplay: true,
        autoplayTimeout: 7000,
        responsiveClass: true,
        responsive:{
            0:{
                items: 1
            },
            575:{
                items: 2
            },
            768:{
                items: 3
            },
            992:{
                items: 4
            }
        }
    });

    $('.blog .owl-carousel').owlCarousel({
        margin: 15,
        rewind: true,
        dots: false,
        nav: false,
        lazyLoad: true,
        autoplay: true,
        autoplayTimeout: 7000,
        responsiveClass: true,
        responsive:{
            0:{
                items: 1
            },
            768:{
                items: 2
            },
            992:{
                items: 3
            }
        }
    });

    if(window.innerWidth>992){
        $('.archive-projs .owl-carousel').owlCarousel({
            margin: 14,
            rewind: true,
            dots: false,
            nav: false,
            lazyLoad: true,
            autoplay: true,
            autoplayTimeout: 7000,
            responsiveClass: true,
            responsive:{
                0:{
                    items: 1
                },
                575:{
                    items: 2
                },
                768:{
                    items: 3
                },
                992:{
                    items: 2
                },
                1200:{
                    items: 3
                }
            }
        });
    }

    $('.post-type-archive-processos .sols .owl-carousel').owlCarousel({
        margin: 15,
        rewind: true,
        dots: false,
        nav: false,
        lazyLoad: true,
        autoplay: true,
        autoplayTimeout: 7000,
        responsiveClass: true,
        responsive:{
            0:{
                items: 1
            },
            575:{
                items: 2
            },
            768:{
                items: 3
            },
            992:{
                items: 4
            }
        }
    });
}

window.addEventListener('scroll',(e)=>{
    if(window.scrollY>106){
        document.querySelector('.sticky').classList.add('scroll');
    }else{
        document.querySelector('.sticky').classList.remove('scroll');
    }
});

document.querySelector('#offcv').addEventListener('show.bs.offcanvas',(e)=>{
    document.querySelector('.navbar-toggler-icon').classList.toggle('toggled');
});
document.querySelector('#offcv').addEventListener('hide.bs.offcanvas',(e)=>{
    document.querySelector('.navbar-toggler-icon').classList.toggle('toggled');
});

document.querySelectorAll('.telp').forEach((telp)=>{
    telp.addEventListener('click',()=>{
        if (telp.dataset.numero){
            let numero = telp.dataset.numero.toString();
            if (numero.length > 10){
                telp.innerHTML = `<a target="_blank" href="https://api.whatsapp.com/send?l=pt_br&amp;phone=55${numero}">(${numero.substr(0, 2)}) ${numero.substr(2, 5)}-${numero.substr(7, 10)}</a>`;
            } else{
                telp.innerHTML = `<a href="tel:+55${numero}">(${numero.substr(0, 2)}) ${numero.substr(2, 4)}-${numero.substr(6, 10)}</a>`;
            }
        }
    });
});

document.querySelectorAll('.mailp').forEach((mailp)=>{
    mailp.addEventListener('click',()=>{
        if (mailp.dataset.email){
            mailp.innerHTML = `<a href="mailto:${mailp.dataset.email}">${mailp.dataset.email}</a>`;
        }
    })
});

document.querySelectorAll('.locp').forEach((locp)=>{
    locp.addEventListener('click',()=>{
        if (locp.dataset.local){
            locp.innerHTML = locp.dataset.local;
        }
    });
});

document.querySelectorAll('#offcv .menu>*.menu-item-has-children').forEach(item=>{
    let newDiv = document.createElement('div');
    let submenu = item.querySelector('.sub-menu');
    let submenuHeight = submenu.offsetHeight;

    submenu.classList.add('closed');
    submenu.style.height = '0px';

    newDiv.classList.add('df');
    newDiv.appendChild(item.children[0]);
    newDiv.insertAdjacentHTML('beforeend','<div class="dropdown"><svg width="16" height="10" viewBox="0 0 16 10" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M0.707031 0.707031L7.70703 7.70703L14.707 0.707031" stroke="var(--footer1)" stroke-width="2"/></svg></div>');
    item.insertAdjacentElement('afterbegin',newDiv);

    item.querySelector('.dropdown').addEventListener('click',()=>{
        submenu.classList.toggle('closed');
        if(submenu.classList.contains('closed')){
            submenu.style.height = '0px';
        }else{
            submenu.style.height = `${submenuHeight}px`;
        }
    });
});

function setCorrectHeights(e = []){
    for(let i of e){
        setTimeout(() => {
            if(document.querySelector(i)){
                let maxHeight = 0;
                document.querySelectorAll(i).forEach(function(e) {
                if (e.offsetHeight > maxHeight) {
                    maxHeight = e.offsetHeight;
                }
                });
                document.querySelectorAll(i).forEach(function(e) {
                    e.style.height = maxHeight + 'px';
                });
            }
        }, 500);
    }
}

if(typeof gtag === 'function'){
    document.querySelectorAll('a[target="_blank"]').forEach((linkk,index)=>{
        linkk.addEventListener('click',()=>{
            gtag('event','clique_link_externo',{
                item_id: index,
                item_name: linkk.textContent,
                item_link: linkk.href
            });
        });
    });
    
    document.querySelectorAll('a[download]').forEach((down,index)=>{
        down.addEventListener('click',()=>{
            gtag('event','clique_download',{
                item_id: index,
                item_name: down.textContent,
                item_download: down.href
            });
        });
    });
    
    document.querySelectorAll('a.telp.zap').forEach((zap,index)=>{
        zap.addEventListener('click',()=>{
            let number = zap.href.replace('/\D/g','');
            gtag('event','contato_por_whatsapp',{
                item_id: index,
                item_name: zap.textContent,
                item_telefone_de_contato: number
            });
        })
    });
    
    document.querySelectorAll('a.mailp').forEach((mail,index)=>{
        mail.addEventListener('click',()=>{
            gtag('event','clique_email',{
                item_id: index,
                item_name: mail.textContent,
                item_email: mail.href
            })
        });
    });
    
    document.querySelectorAll('.rss').forEach((rss,index)=>{
        rss.querySelectorAll('.rs').forEach((_rs,_index)=>{
            _rs.addEventListener('click',()=>{
                gtag('event','clique_para_rede_social',{
                    item_parent_id: index,
                    item_id: _index,
                    item_name: _rs.getAttribute('aria-label'),
                    item_link: _rs.href
                })
            });
        });
    });
}

document.querySelectorAll('.magicscroll').forEach((magicscroll)=>{
    magicscroll.addEventListener('click',(e)=>{
        e.preventDefault();
        let id = magicscroll.getAttribute('href');
        let targetOffset;
        let limit = 80;

        if(id.indexOf('#')!== -1){
            if(document.querySelector(id)){
                targetOffset = document.querySelector(id).offsetTop;
                if(document.documentElement.scrollTop >= 100){
                    limit = 100;
                }
                window.scrollTo({
                    top: targetOffset - limit,
                    behavior: 'smooth'
                });
            }else{
                window.location = window.location.protocol + '//' + window.location.hostname + '/' + id;
            }
        }else{
            window.location = id;
        }
    });
});