/** @odoo-module */
import {VideoSelector} from "@web_editor/components/media_dialog/video_selector";
import { Component, xml, useState, useRef, onWillStart, useEffect } from "@odoo/owl";
import { useService } from '@web/core/utils/hooks';
import { patch } from "@web/core/utils/patch";


patch(VideoSelector.prototype,{
    setup(){
        super.setup()
        this.fileInput = useRef('v-file-input');
        this.orm = useService('orm');
        this.uploadService = useService('upload');
        this.notificationService = useService("notification");
        this.PLATFORMS['local']='local'
        this.OPTIONS['autoplay']['platforms'].push('local')
        this.OPTIONS['loop']['platforms'].push('local')
        this.OPTIONS['hide_controls']['platforms'].push('local')
    },
    onClickUpload() {
        this.fileInput.el.click();
    },
    async onUploaded(attachment) {
        const host = window.location.host
        const attId = attachment.id
        if (!attId)
            return
        const localUrl = `/player/local/${attId}`
        this.state.urlInput = localUrl
        await this.updateVideo(localUrl)
    },
    async onChangeFileInput() {
        const inputFiles = this.fileInput.el.files;
        if (!inputFiles.length) {
            return;
        }
        await this.uploadService.uploadFiles(inputFiles, { resModel: this.props.resModel, resId: this.props.resId }, attachment => this.onUploaded(attachment));
        this.fileInput.el.value = '';
    },
    localVideoUrlEncode(url,options){
        let params = {}
        params['autoplay'] = options['autoplay']?1:0
        params['loop'] = options['loop']?1:0
        params['controls'] = options['hide_controls']?0:1
        const query = new URLSearchParams(params).toString()
        const mainUrl = url.split('?')[0]
        return `${mainUrl}?${query}`
    },
    async _getVideoURLData(url, options){
        if (url.indexOf('/player/local')>-1){
            const embedUrl = this.localVideoUrlEncode(url,options)
            return Promise.resolve({
                embed_url:embedUrl,
                video_id:this.props.resId,
                params:{},
                platform:'local'
            })
        }
        return super._getVideoURLData(url,options)
    }

})
